# SPEC: CYCLE02 - Integration & QA Orchestration

## Summary

This second cycle completes the transition to the Nitpickers 5-Phase Architecture. While CYCLE01 established the parallelizable foundation (Phase 2), CYCLE02 focuses on safely merging those divergent implementations and executing the final multi-modal User Acceptance Testing (UAT) validations. Our objective is to construct the new `Integration Graph` (Phase 3) and refine the standalone `QA Graph` (Phase 4).

The core challenge in this cycle lies in the intelligent resolution of Git merge conflicts. Instead of relying on raw, contextless conflict markers (`<<<<<<<`), we will develop a sophisticated 3-Way Diff mechanism within `conflict_manager.py`. This mechanism will extract the common ancestor (Base), the Local branch, and the Remote branch modifications, packaging them into a highly structured prompt for a "Master Integrator" LLM. This ensures conflicts are resolved with a full understanding of the original architectural intent.

Following successful integration, the entire merged codebase must be subjected to a global sandbox execution (`global_sandbox_node`). Only after this stringent blockade is passed will the system proceed to Phase 4 (QA Graph), where automated Playwright E2E tests will run. If these tests fail, a stateless "QA Auditor" equipped with Vision capabilities will diagnose the screenshots and logs, forming a self-healing loop. Finally, the orchestration logic in `src/cli.py` and `src/services/workflow.py` must be updated to seamlessly connect these disparate phases into a unified execution pipeline.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)

The Integration and QA phases rely on advanced Vision Language Models to diagnose frontend UI failures. The following external service secrets must be explicitly appended to the target project's `.env.example` file, demarcated by a `# Target Project Secrets` comment.

-   `OPENROUTER_API_KEY`: Required for the QA Auditor and UX Auditor (Vision models) to analyze Playwright screenshots.
-   `JULES_API_KEY`: Required for the Master Integrator and QA Session worker agents.
-   `E2B_API_KEY`: Required to execute the global sandbox and the final Playwright E2E tests securely.

The Coder must ensure these keys are represented as empty placeholders to guide user configuration securely.

### B. System Configurations (`docker-compose.yml`)

The operation of the 3-Way Diff and the Playwright test suite requires specific non-confidential environmental setups. The Coder must inject the following configurations directly into the `environment:` section of the relevant service within the target project's `docker-compose.yml`.

-   `NITPICK_ENABLE_VISION_AUDIT=true`: Toggles the invocation of the Vision LLM during the QA phase.
-   `PLAYWRIGHT_BROWSERS_PATH=/ms-playwright`: Ensures the sandbox has access to the pre-installed headless browsers.

The Coder is explicitly instructed to strictly preserve valid YAML formatting and idempotency during this operation.

### C. Sandbox Resilience

**MANDATE MOCKING:** To guarantee sandbox resilience, the Coder MUST explicitly instruct that all external API calls relying on the newly defined secrets in `.env.example` MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`).

*Why:* The Sandbox evaluating the system's integration logic will not possess the real API keys during autonomous test runs. If tests attempt real network calls to OpenRouter or Jules APIs without valid `.env` values, the pipeline will immediately fail. Strict mocking is essential for validating the 3-Way Diff logic and the Graph routing without network side-effects.

## System Architecture

This section details the exact code blueprints required for orchestrating the Integration and QA phases.

### File Structure Modifications

The following ASCII tree outlines the files to be created or modified in this cycle, completing the System Architecture blueprint.

```text
src/
├── **cli.py**                  # Modification: Update run-pipeline to execute Phases 1-4 sequentially
├── **graph.py**                # Modification: Implement _create_integration_graph and adjust _create_qa_graph
├── nodes/
│   └── **routers.py**          # Modification: Implement route_merge, route_global_sandbox
└── services/
    ├── **conflict_manager.py** # Modification: Implement 3-Way Diff extraction via Git commands
    ├── **uat_usecase.py**      # Modification: Decouple from Phase 2, adjust state inputs for Phase 4
    └── **workflow.py**         # Modification: Orchestrate build_integration_graph and build_qa_graph
```

## Design Architecture

The structural integrity of the integration process relies on rigid Pydantic schemas. The modifications below blueprint the necessary components.

### 1. `src/state.py` (Domain Concepts & Constraints)

The `IntegrationState` manages the concurrent merging of parallel branches.

**Domain Concept:** Represents the state of the Phase 3 integration attempt. It tracks the branches awaiting merge and maintains a registry of any conflicts encountered during the process.

**Key Invariants & Validation Rules:**
-   `branches_to_merge` (list[str]): Must be strongly typed. Lists the branches (Cycle 1...N) that need to be merged into the integration branch.
-   `unresolved_conflicts` (list[ConflictRegistryItem]): Maintains a list of files that failed the standard Git merge and require the Master Integrator.
-   Must utilize `ConfigDict(extra="forbid", validate_assignment=True)` to prevent arbitrary state pollution.

### 2. `src/services/conflict_manager.py` (Producers & Consumers)

This service consumes standard Git conflicts and produces a structured 3-Way Diff prompt package.

**Domain Concept:** The `ConflictManager` safely resolves Git conflicts by providing the LLM with the complete architectural context rather than raw conflict markers.

**Key Invariants & Validation Rules:**
-   `build_conflict_package(file_path: str) -> str`:
    -   Must execute `git show :1:{file_path}` to retrieve the Base (common ancestor) code.
    -   Must execute `git show :2:{file_path}` to retrieve the Branch A (Local) modifications.
    -   Must execute `git show :3:{file_path}` to retrieve the Branch B (Remote) modifications.
    -   Must format these three strings into a unified Markdown prompt template explicitly instructing the "Master Integrator" to safely combine the intents without data loss.

### 3. `src/nodes/routers.py` (Producers & Consumers)

**Key Invariants & Validation Rules:**
-   `route_merge(state: IntegrationState) -> str`:
    -   If `unresolved_conflicts` is not empty, return `"conflict"` (routes to `master_integrator_node`).
    -   If empty, return `"success"` (routes to `global_sandbox_node`).
-   `route_global_sandbox(state: IntegrationState) -> str`:
    -   If the global test suite fails, return `"failed"` (routes to a remediation node or fails the phase).
    -   If successful, return `"pass"` (routes to END of Phase 3).

## Implementation Approach

1.  **Phase 1: 3-Way Diff Logic Implementation**
    -   Open `src/services/conflict_manager.py`. The `scan_conflicts` method can remain largely intact.
    -   Implement the new `build_conflict_package` method. Utilize the internal `ProcessRunner` (or `subprocess`) to execute the `git show :X:` commands to extract the Base, Local, and Remote file states.
    -   Construct the specific prompt template defined in the requirement specification and return the formatted string.
2.  **Phase 2: Integration Graph Construction**
    -   Open `src/graph.py`. Implement the `_create_integration_graph` method.
    -   Define the nodes: `git_merge_node` (attempts standard merge), `master_integrator_node` (uses the conflict package LLM prompt), and `global_sandbox_node` (runs full test suite).
    -   Add the conditional edges using the new router functions defined in the Design Architecture.
3.  **Phase 3: QA Graph Decoupling & Orchestration**
    -   Open `src/services/uat_usecase.py`. Remove any legacy triggers that invoked this process during the Phase 2 (Coder) loops. Adjust its input signatures to strictly accept the post-integration state.
    -   Open `src/cli.py` and `src/services/workflow.py`. Update the `run_pipeline` orchestration flow.
    -   Ensure `WorkflowService` concurrently executes all `build_coder_graph` instances.
    -   Implement a synchronization point (e.g., `asyncio.gather`) waiting for all PRs to complete.
    -   Invoke `build_integration_graph`. Upon successful completion, invoke `build_qa_graph`.

## Test Strategy

A robust test suite is critical to validate the deterministic behavior of the Integration and QA Graphs.

### Unit Testing Approach (Min 300 words)

The primary focus of the unit tests will be to validate the strict routing logic and the precise execution of the 3-Way Diff Git commands. We must guarantee that the conditional edge functions in `src/nodes/routers.py` operate flawlessly under various state conditions.

We will write dedicated test cases for `route_merge`, injecting mock `IntegrationState` objects with populated and empty `unresolved_conflicts` lists, ensuring they return `"conflict"` and `"success"` respectively.

The most critical unit tests will target `ConflictManager.build_conflict_package`. Since we cannot rely on a real external Git repository during unit tests, we will employ a strict Zero-Mock Policy for internal logic but utilize `unittest.mock.patch` on the underlying `ProcessRunner.run_command` method. We will mock the subprocess calls for `git show :1:`, `:2:`, and `:3:` to return predefined strings representing a Base file, Branch A modifications, and Branch B modifications. The test will then assert that the final returned string accurately templates these three distinct code blocks into the required "Master Integrator" prompt format, verifying the core 3-Way Diff logic without actual file system access.

### Integration Testing Approach (Min 300 words)

The integration tests will evaluate the interaction between the newly wired LangGraph nodes within the `_create_integration_graph` structure. We will compile the graph (`build_integration_graph`) and execute it using a mock Checkpointer.

To ensure sandbox resilience and adhere strictly to the "Mandate Mocking" rule, all external LLM invocations within the node functions (e.g., `master_integrator_node`) MUST be mocked. The tests will not perform real HTTP calls to the LLM providers.

We will trace the execution path of the integration graph. For example, we will inject a state simulating an unresolved conflict and verify the graph correctly routes to the `master_integrator_node`. We will mock the LLM response to simulate a successful resolution, update the mock state, and trace the path back to the `git_merge_node`. Finally, we will simulate a successful `global_sandbox_node` evaluation to ensure the Phase 3 graph terminates correctly at the END state. This ensures the structural integrity of the integration pipeline without incurring any external API dependency risks. Any tests requiring persistent Git state setup MUST utilize Pytest fixtures that initialize a temporary local bare repository and roll it back after the test.
