# CYCLE02 Specification: Integration Phase, UAT Phase, & CLI Orchestration

## Summary
The primary objective of CYCLE02 is to fully implement the overarching pipeline execution architecture, specifically establishing Phase 3 (Integration Graph), Phase 4 (QA Graph), and the central CLI orchestrator logic. Previously, the mechanisms for code integration and End-to-End Quality Assurance (QA) were not cleanly decoupled from the parallel feature branches. This update rectifies that architectural flaw by completely separating them into distinct, sequential LangGraph phases.

By designing `_create_integration_graph` to aggregate and merge parallel cycle PRs using a sophisticated 3-Way Diff context, we empower the AI to intelligently resolve Git conflicts rather than naively failing. Furthermore, by isolating `_create_qa_graph` to execute Playwright tests and invoke external Vision/QA Auditors specifically on the globally integrated codebase, we ensure that frontend regressions are caught definitively before deployment. Finally, the CLI orchestrator (`run-pipeline`) is completely overhauled to manage this 5-Phase flow, explicitly spinning up parallel Phase 2 tasks, rigidly awaiting their full completion via `asyncio.gather`, executing Phase 3 sequentially, and subsequently concluding with the Phase 4 UI validation layer.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
This cycle inherently requires high-capacity external API keys to resolve multi-modal vision diagnostics (for UI failure screenshots) and to intelligently merge complex overlapping code snippets via the primary LLM agents.
- **Required System Secrets:**
  - `JULES_API_KEY`
  - `OPENROUTER_API_KEY`
  - `E2B_API_KEY`
- Explicitly instruct the Coder to append these keys to `.env.example` with clear `# Target Project Secrets` comments if any new external services are referenced during the development of the Integration or QA graphs.

### B. System Configurations (`docker-compose.yml`)
- No immediate non-confidential environmental setups are required for this specific cycle beyond the existing Docker networking configuration.
- However, instruct the Coder to place these directly into the `environment:` section of the relevant service in `docker-compose.yml` if newly discovered settings apply during the QA setup phase (e.g., Playwright browser configurations or virtual framebuffers).
- Explicitly instruct the Coder to preserve valid YAML formatting and idempotency. Do not overwrite existing agent configurations; only append target project variables.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
- **Mandate Mocking:** *All external API calls relying on the newly defined secrets in `.env.example` MUST be rigidly mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`).*
- **Why:** The Sandbox will not possess the real API keys during the autonomous evaluation phase. If tests attempt real network calls to SaaS providers without valid `.env` values, the pipeline will fail and cause an infinite retry loop. Testing the integration logic, the complex 3-Way Diff prompts, and the CLI orchestrator must strictly bypass any live OpenAI, Anthropic, or external API calls. The testing suite must remain 100% deterministic and hermetic.

## System Architecture

The following file modifications are strictly required to enact the robust orchestration for Phase 3 & 4. This phase moves beyond the isolated branches and focuses on the global repository state. The architecture demands that the CLI acts as the ultimate controller, sequentially firing entire LangGraph objects only when the prerequisite phases succeed.

```text
/
└── src/
    ├── **cli.py**                 # Target: Update CLI orchestrator commands to manage Phase 2 parallelization and Phase 3/4 sequential execution.
    ├── **graph.py**               # Target: Define and wire the _create_integration_graph and _create_qa_graph explicitly.
    └── services/
        ├── **conflict_manager.py** # Target: Implement the sophisticated 3-Way Diff Git extraction builder logic.
        ├── **uat_usecase.py**      # Target: Decouple the QA runner entirely from Phase 2 to serve Phase 4.
        └── **workflow.py**         # Target: Implement the main run_pipeline orchestrator utilizing asyncio.gather.
```

The data flow is centralized in `workflow.py`. It initiates multiple asynchronous instances of the Phase 2 graph. It then aggregates their resulting success branches into a new `IntegrationState` object. This state is passed into the Phase 3 graph. If the `master_integrator_node` successfully eliminates all Git conflict markers and passes the `global_sandbox_node`, the flow proceeds to Phase 4.

## Design Architecture

### Pydantic Models and Invariants
This system is strictly designed with Pydantic-based schema control. Phase 3 (Integration) fundamentally operates on the newly established `IntegrationState`, entirely distinct from the `CycleState` used in Phase 2.

**Variables to Manage (`IntegrationState` in `src/state.py`):**
- `branches_to_merge`: A highly-typed list of strings representing the names of the Git branches successfully originating from the parallel Phase 2 cycles.
- `unresolved_conflicts`: A structured list of `ConflictRegistryItem` objects. These objects pinpoint exactly which files contain unresolvable Git markers (e.g., `<<<<<<<`, `=======`, `>>>>>>>`) after a naive merge attempt.
- `master_integrator_session_id`: A persistent string identifier ensuring the LLM context remains stable during complex, multi-turn conflict resolution sessions, preventing the AI from losing track of the file modifications.

**Invariants, Constraints, and Validation Rules:**
- `IntegrationState` is entirely decoupled from `CycleState`. Only one instance ever runs across all combined parallel branches. It serves as the single source of truth for the entire integration lifecycle.
- `ConflictManager.build_conflict_package` must securely validate file paths within the workspace boundary. It must strictly read file contents using asynchronous Git sub-processes (e.g., `git show`) to avoid dangerous directory traversal vulnerabilities.
- Consumers of Phase 3 output are inherently the Phase 4 QA processes. Phase 4 strictly requires the `global_sandbox_node` to pass with an exit code of `0` in Phase 3 before it ever triggers. If Phase 3 fails, the pipeline halts immediately.

## Implementation Approach

### 1. Update `src/services/conflict_manager.py` (3-Way Diff)
Ensure the `build_conflict_package` method is significantly upgraded. It must retrieve three distinct states of the conflicted file, not just the raw file with conflict markers:
- `Base`: The common ancestor of the two branches (`git show :1:{file_path}`).
- `Local`: The current integration branch modification (`git show :2:{file_path}`).
- `Remote`: The incoming feature branch modification (`git show :3:{file_path}`).
Construct a comprehensive text prompt instructing the `Master Integrator` to intelligently generate a unified final code block without `<<<<<<<` markers. Use the existing validated prompt template `MASTER_INTEGRATOR_PROMPT.md` if available, interpolating the three raw code strings clearly.

### 2. Implement `_create_integration_graph` (`src/graph.py`)
- Wire the nodes strictly in the following sequential order: `git_merge_node` -> `master_integrator_node` -> `global_sandbox_node`.
- Add intelligent conditional routing logic:
  - If `git_merge_node` detects unresolvable conflicts, route the loop securely to `master_integrator_node`. The graph must loop between these two until `git_merge_node` reports no more conflict markers exist.
  - If `global_sandbox_node` fails due to syntax errors introduced post-merge, route the flow securely back to an `integration_fixer_node` or `master_integrator_node` to rectify the broken syntax.

### 3. Orchestrate with `WorkflowService` (`src/services/workflow.py`) & `src/cli.py`
Refactor the `run_pipeline` orchestration mechanism to act as the master controller for the 5-Phase architecture:
- **Phase 2 (Parallel Execution):** Execute each configured Coder cycle fully asynchronously. The orchestrator must aggressively await `asyncio.gather` for all `_create_coder_graph` instances to reach `END` before progressing.
- **Phase 3 (Sequential Execution):** Instantiate `_create_integration_graph`. Provide the compiled list of successfully generated PRs/branches into the `IntegrationState`. Run the integration process completely sequentially to `END`.
- **Phase 4 (Sequential Execution):** If and only if Phase 3 completes entirely successfully, instantiate `_create_qa_graph` to run the final E2E UAT tests against the integrated codebase.

## Test Strategy

Testing this orchestration layer requires ensuring that the asynchronous tasks do not leak state and that the integration loop handles fatal Git conflicts gracefully without hanging the CI pipeline indefinitely.

### Unit Testing Approach
- Develop comprehensive tests in `tests/test_conflict_manager.py`.
- Ensure criteria from the Design Architecture are met by mocking `ProcessRunner.run_command` via `unittest.mock.AsyncMock` to cleanly return simulated git outputs for Base, Local, and Remote stages without actually cloning repositories.
- Assert that `build_conflict_package` correctly interpolates the mocked Git data into the resulting prompt package string exactly as specified by the markdown prompt template.
- Develop tests in `tests/test_workflow.py` to specifically test the asynchronous `asyncio.gather` orchestration logic. Mock the individual graph builders and assert they are correctly spawned in parallel and strictly awaited before the Phase 3 integration graph is initiated.

### Integration Testing Approach
- Develop robust, end-to-end integration tests in `tests/test_integration_graph.py`.
- Instantiate the actual compiled `_create_integration_graph` using the `MemorySaver` checkpointer to observe state mutations during execution.
- Create mock implementations of `git_merge_node` to forcefully inject a simulated `ConflictRegistryItem` containing hard `<<<<<<<` markers into the `IntegrationState`.
- Mock `master_integrator_node` to smoothly resolve the conflict by replacing the file contents with clean, unified code.
- Assert that the graph successfully and sequentially transitions: `git_merge_node` -> `master_integrator_node` -> `git_merge_node` (where it confirms the conflict is gone) -> `global_sandbox_node` -> `END`.
- This ensures the 3-Way Diff resolution loop handles failures gracefully and explicitly does not loop infinitely.
