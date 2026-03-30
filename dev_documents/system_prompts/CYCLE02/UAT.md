# CYCLE02 UAT Plan

## Test Scenarios

### Scenario 1: Successful 3-Way Diff Integration (Priority: High)
The primary objective of this scenario is to validate the automated resolution of a simulated Git merge conflict utilizing the `master_integrator_node` and its 3-Way Diff logic.

### Scenario 2: Global Sandbox Validation After Merge (Priority: High)
This scenario ensures that the system correctly transitions from a successful merge to the `global_sandbox_node` and validates that the integrated code passes the final system-wide checks.

### Behavior Definitions

**Scenario 1: Successful 3-Way Diff Integration**

GIVEN a simulated `IntegrationState` containing a file with conflicting modifications in Branch A and Branch B
AND the underlying repository reflects a Git merge conflict state
WHEN the `_create_integration_graph` is executed
AND the `git_merge_node` detects the conflict
THEN the workflow should route to the `master_integrator_node`
AND the `ConflictManager` should successfully extract the Base, Branch A, and Branch B code via `git show`
AND the node should process the mocked resolution
AND the workflow should loop back to `git_merge_node` successfully

**Scenario 2: Global Sandbox Validation After Merge**

GIVEN a successful resolution in the `git_merge_node`
WHEN the workflow transitions to the `global_sandbox_node`
AND the `global_sandbox_node` executes the project's entire static analysis suite (e.g., `uv run pytest`, `uv run ruff check`)
THEN the node should return a "pass" status
AND the overall Integration Phase should complete successfully
