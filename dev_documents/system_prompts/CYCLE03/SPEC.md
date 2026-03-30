# CYCLE 03: Phase 3 Integration Graph (3-Way Diff)

## Summary
The goal of Cycle 03 is to establish a dedicated Phase 3 (Integration Phase) capable of autonomously resolving Git merge conflicts generated during the concurrent execution of Phase 2 cycles.

Instead of relying on standard text-based Git conflict markers (which confuse LLMs), this cycle implements a true 3-Way Diff resolution strategy. The `ConflictManager` will be updated to fetch the common ancestor (Base), the integration branch (Local), and the feature branch (Remote) contents, packaging them into a structured prompt for the Master Integrator agent. A dedicated `_create_integration_graph` will orchestrate this process and validate the merged result using a Global Sandbox.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
*Target Project Secrets:* No new external APIs are introduced. Existing keys (JULES_API_KEY) are sufficient for the Master Integrator.

### B. System Configurations (`docker-compose.yml`)
*Non-confidential configurations:* Ensure the Sidecar path variables are maintained.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
*Mandate Mocking:* You MUST explicitly instruct the Coder that *all external API calls relying on the newly defined secrets in `.env.example` MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*.
The `ConflictManager` will execute real Git commands. These commands MUST be mocked or executed against a real, isolated, temporary bare Git repository (`pyfakefs` or `tempfile`) in the test suite to prevent destructive actions on the actual project repository during autonomous evaluation.

## System Architecture

The following file structure must be implemented or modified to support Phase 3 integration:

```text
src/
├── **state.py**                  # Ensure IntegrationState exists and is properly configured.
├── **graph.py**                  # Implement _create_integration_graph.
└── services/
    └── **conflict_manager.py**   # Implement 3-Way Diff package generation.
```

## Design Architecture

This cycle focuses on generating a structured 3-Way Diff package and orchestrating the integration process.

1.  **`src/services/conflict_manager.py` (`build_conflict_package`)**:
    *   **Domain Concept**: Responsible for gathering the exact state of conflicting files.
    *   **Invariants**:
        *   Must reliably execute `git show :1:{file_path}` to retrieve the base version.
        *   Must reliably execute `git show :2:{file_path}` to retrieve the local (integration branch) version.
        *   Must reliably execute `git show :3:{file_path}` to retrieve the remote (feature branch) version.
        *   Must package these into a structured prompt string or Pydantic model for the LLM.
    *   **Consumers**: `master_integrator_node` in the Integration Graph.

2.  **`src/graph.py` (`_create_integration_graph`)**:
    *   **Domain Concept**: Orchestrates the sequential merging, resolution, and validation of branches.
    *   **Constraints**:
        *   Must use `IntegrationState` (not `CycleState`).
        *   Must start with `git_merge_node`.
        *   Must conditionally route (`route_merge`) to `master_integrator_node` on conflict, or `global_sandbox_node` on success.
        *   `master_integrator_node` must loop back to `git_merge_node`.
        *   `global_sandbox_node` must conditionally route (`route_global_sandbox`) to `END` on success, or back to a fixer node on failure.

## Implementation Approach

1.  **Update `ConflictManager`**: Open `src/services/conflict_manager.py`. Refactor the conflict generation logic to construct a 3-way diff prompt. Use `ProcessRunner` to execute `git show` commands asynchronously. Handle cases where a file might have been added or deleted (e.g., `:1` missing).
2.  **Implement `_create_integration_graph`**: Open `src/graph.py`. Locate (or create) the `_create_integration_graph` method.
    *   Initialize a `StateGraph(IntegrationState)`.
    *   Add nodes: `git_merge_node`, `master_integrator_node`, `global_sandbox_node`.
    *   Add unconditional edge: START -> `git_merge_node`.
    *   Add conditional edge from `git_merge_node` using `route_merge` (or similar). Route to `master_integrator_node` ("conflict") or `global_sandbox_node` ("success").
    *   Add unconditional edge: `master_integrator_node` -> `git_merge_node` (to attempt merge again after resolution).
    *   Add conditional edge from `global_sandbox_node` routing to `END` ("pass") or a failure handler ("failed").
3.  **Ensure Routing Support**: If `route_merge` or `route_global_sandbox` are missing, implement them in `src/nodes/routers.py` to evaluate the `conflict_status` within `IntegrationState`.

## Test Strategy

All tests must be executed without real LLM API calls, strictly using local, mocked dependencies.

**Unit Testing Approach (Min 300 words):**
We must test the `build_conflict_package` logic within `ConflictManager` extensively. Create tests in `tests/unit/services/test_conflict_manager.py`.
*   **Test 3-Way Diff Generation**: Mock `ProcessRunner.run_command` (or equivalent) to return predefined file contents for `:1`, `:2`, and `:3`. Execute `build_conflict_package`. Assert that the generated prompt correctly embeds the Base, Local, and Remote code blocks in the expected format.
*   **Test Missing Ancestor**: Mock `ProcessRunner` to simulate an error when fetching `:1` (simulating a file added independently on both branches). Assert the function handles this gracefully, potentially omitting the Base block or indicating it is a newly added file.

**Integration Testing Approach (Min 300 words):**
We must test the `_create_integration_graph` flow using deterministic mocks. Create tests in `tests/integration/test_integration_graph.py`.
*   **Test Clean Merge Path**: Mock `git_merge_node` to succeed instantly. Execute the graph. Verify the execution trace hits `git_merge_node`, routes to `global_sandbox_node`, and terminates at `END`.
*   **Test Conflict Resolution Loop**: Mock `git_merge_node` to return a "conflict" status initially, and "success" on the second invocation. Mock `master_integrator_node` to simulate successful resolution. Execute the graph. Verify the trace loops: `git_merge_node` -> `master_integrator_node` -> `git_merge_node` -> `global_sandbox_node` -> `END`. Use an `AsyncMock` for node execution to prevent coroutine warnings.