# CYCLE01: 5-Phase Workflow Implementation

## Summary
The primary objective of CYCLE01 is to refactor the existing LangGraph execution flow into a well-defined, modular "5-Phase" pipeline, as detailed in the `SYSTEM_ARCHITECTURE.md`. This requires significant structural enhancements across the system to support a robust, zero-trust validation workflow. The implementation encompasses the augmentation of Pydantic state models in `src/state.py` to handle serial auditing and refactoring loops, and the redesign of graph routing logic in `src/graph.py` and `src/nodes/routers.py` to accommodate the newly defined phases.

A critical component of this cycle is the introduction of the Integration Phase (Phase 3). This phase handles the automated merging of parallel development branches and incorporates an intelligent 3-Way Diff conflict resolution strategy within `src/services/conflict_manager.py`. The Master Integrator agent will be designed to synthesize conflicting changes safely, ensuring the intentions of both branches are preserved. Furthermore, the orchestrator in `src/services/workflow.py` and `src/cli.py` will be overhauled to seamlessly manage the execution sequence: running Coder Graph cycles in parallel, synchronizing for the Integration Phase, and finally triggering the UAT & QA Graph for comprehensive end-to-end testing. The completion of this cycle will result in a highly stable, decoupled architecture capable of reliably automating complex software development tasks with continuous, self-healing validation.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
The Coder must append the following external service secrets to `.env.example`.
- `E2B_API_KEY`: Required for executing the dynamic sandbox evaluation securely.
- `JULES_API_KEY`: Required for the primary Coder, Master Integrator, and Architect LLM agents.
- `OPENROUTER_API_KEY`: Required for the stateless Auditor and QA diagnostic agents.

*Coder Instruction:* Append these explicitly with a `# Target Project Secrets` comment in the `.env.example` file.

### B. System Configurations (`docker-compose.yml`)
No new system configurations or executable setups are required for this specific cycle within `docker-compose.yml`.

*Coder Instruction:* Ensure any existing configurations remain intact and valid YAML formatting is preserved. Do not overwrite existing agent configurations.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
**Mandate Mocking:** You MUST explicitly mock all external API calls relying on the newly defined secrets in `.env.example` in unit and integration tests (using `unittest.mock` or `pytest-mock`).

*Why:* The Sandbox will not possess the real API keys during the autonomous evaluation phase. If tests attempt real network calls to SaaS providers without valid `.env` values, the pipeline will fail and cause an infinite retry loop. This is critical to ensure zero-side-effect test executions in the CI/CD pipeline.

## System Architecture
The refactoring modifies existing files while adding minimal new ones, focusing on state and graph execution.

```text
src/
├── **state.py**
├── **graph.py**
├── nodes/
│   └── **routers.py**
└── services/
    ├── **conflict_manager.py**
    ├── **uat_usecase.py**
    └── **workflow.py**
```

The system will leverage existing foundations to implement the 5-phase structure:
1. **Phase 0 & 1**: The init and planning phases are already conceptualized. The Architect graph will output the plans.
2. **Phase 2 (Coder Graph)**: Modification of `_create_coder_graph` in `src/graph.py` is central. It must incorporate the `coder_session`, `self_critic` (initial), `sandbox_evaluate`, `auditor_node` (serial execution based on `current_auditor_index`), `refactor_node`, and `final_critic_node`.
3. **Phase 3 (Integration Graph)**: The new `_create_integration_graph` will contain the `git_merge_node`, `master_integrator_node`, and `global_sandbox_node`. The `master_integrator_node` will utilize the enhanced `ConflictManager` to resolve 3-Way diffs.
4. **Phase 4 (UAT & QA Graph)**: `_create_qa_graph` will be separated from Phase 2. `src/services/uat_usecase.py` will handle triggering this graph only after Phase 3 concludes successfully.
5. **Orchestration**: `src/services/workflow.py` coordinates the parallel execution of Coder cycles and subsequent synchronization for Integration and UAT phases.

## Design Architecture
This section outlines the Pydantic-based schema design to ensure robust state tracking throughout the LangGraph execution.

**Domain Concepts & Schemas (`src/state.py`):**
- **CycleState / CommitteeState Modification**:
  - `is_refactoring: bool`: Determines if the process is in the final polish loop post-audit (default: `False`).
  - `current_auditor_index: int`: Tracks the progression through the series of auditors, typically 1 to 3 (default: `1`).
  - `audit_attempt_count: int`: Tracks rejection counts from a single auditor to prevent infinite loops (default: `0`).
- **IntegrationState (New/Expanded)**:
  - `branches_to_merge: list[str]`: A list of successful cycle branches pending integration into the main branch.
  - `conflict_files: list[str]`: Tracks files currently in a conflicted state requiring resolution.

**Key Invariants & Constraints:**
- The `audit_attempt_count` must strictly cap at a defined threshold (e.g., 2) before forcing a transition or specific fallback.
- The `current_auditor_index` should logically progress only when `Approve` is received.
- `IntegrationState` requires absolute paths or strictly validated relative paths for `conflict_files` to avoid directory traversal risks during Git operations. To prevent directory traversal and prefix attacks, all file and repository paths within `ConflictManager` must be rigorously validated using `path.resolve(strict=False).is_relative_to(settings.paths.workspace_root.resolve(strict=True))`.
- When typing fields that may receive mocks, enforce the use of `Annotated[..., SkipValidation]` rather than reverting to `Any`.

**Expected Consumers:**
- The routing functions in `src/nodes/routers.py` will heavily consume these states to direct graph edges dynamically.
- The Orchestrator (`workflow.py`) will consume the aggregated outputs of all `CycleState`s to build the `IntegrationState`.

## Implementation Approach
1. **State Enhancement (`src/state.py`)**: Define the new boolean and integer fields in the primary `CycleState` or `CommitteeState` Pydantic models. Create or refine the `IntegrationState` to manage merging operations.
2. **Routing Logic (`src/nodes/routers.py`)**: Implement `route_sandbox_evaluate` (evaluating `is_refactoring`), `route_auditor` (managing `current_auditor_index` and `audit_attempt_count`), and `route_final_critic`.
3. **Graph Rewiring (`src/graph.py`)**: Reconstruct `_create_coder_graph` to establish the serial audit loop and refactor node. Construct `_create_integration_graph` to handle the merge nodes. Update the UAT triggers to ensure `_create_qa_graph` executes independently.
4. **3-Way Diff Resolution (`src/services/conflict_manager.py`)**: Refactor `build_conflict_package` to construct a comprehensive prompt including Base (common ancestor), Local (Branch A), and Remote (Branch B) code blocks via specific Git commands (e.g., `git show :1:file`). **Critically**, to avoid blocking calls in async functions and partial executable paths (Ruff `ASYNC221`, `S607`), use the project's asynchronous `ProcessRunner` or `asyncio.create_subprocess_exec` along with `shutil.which()` to resolve absolute paths when executing system commands asynchronously.
5. **Orchestration Refinement (`src/services/workflow.py`)**: Implement asynchronous, parallel execution of the `_create_coder_graph` for all detected cycles. Implement a barrier synchronization point before sequentially triggering the integration and UAT graphs.

## Test Strategy
**Unit Testing Approach (Min 300 words):**
The core validation logic resides within the routing functions and state models. We will employ comprehensive unit tests using Pytest. For `src/state.py`, we will instantiate `CycleState` and `IntegrationState` with various valid and invalid boundary conditions, verifying that Pydantic enforces the schema correctly (e.g., ensuring `current_auditor_index` defaults to 1). The routing functions in `src/nodes/routers.py` will be tested by passing mocked state dictionaries simulating different scenarios: a failed sandbox evaluation, a successful evaluation requiring an audit, and a successful evaluation post-refactor requiring final critique. We will strictly assert the returned string route (e.g., "auditor", "failed", "final_critic"). For `src/services/conflict_manager.py`, the `build_conflict_package` will be tested by mocking the Git subprocess runner (`ProcessRunner`) to simulate returning the Base, Local, and Remote versions of a file, verifying the constructed string correctly embeds these three distinct sections without executing real shell commands. All unit tests must explicitly use `unittest.mock` to stub external calls and avoid side effects.

**Integration Testing Approach (Min 300 words):**
Integration tests will focus on the actual LangGraph transitions and the workflow orchestrator. We will construct a minimal, mocked version of the `_create_coder_graph` using `pytest` fixtures, intercepting the LLM generation nodes to return deterministic "Approve" or "Reject" payloads. We will simulate a full loop, validating that `audit_attempt_count` increments on rejection and that the graph successfully transitions to the `refactor_node` once all auditors pass. For `_create_integration_graph`, we will establish a temporary, bare Git repository using `pytest.fixture(scope="function")`. We will programmatically create a base commit and two diverging, conflicting commits. We will then invoke the Integration graph logic, mocking the `master_integrator_node` to return a unified resolution, and verify that the system successfully commits the resolved file. The orchestrator in `src/services/workflow.py` will be tested by simulating multiple dummy cycles, asserting that it correctly parallelizes the coder executions and effectively blocks until all complete before invoking the integration logic. We will ensure all actual external APIs (e.g., OpenRouter, JULES) are mocked out completely to adhere to the Sandbox Resilience constraint.
