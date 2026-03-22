# CYCLE02 UAT: Integration Graph & 3-Way Diff

## Test Scenarios

### Scenario ID: Integration_Phase_01 - Clean Merge
- **Priority**: High
- **Description**: Verify that the Integration Graph correctly processes a merge between two branches that do not have any conflicting changes. This is the baseline "happy path" for Phase 3. The system must attempt a Git merge, detect no conflicts, and immediately route to the Global Sandbox node. The Global Sandbox must then execute the full suite of static analysis (Ruff, Mypy) and unit tests (Pytest) on the integrated codebase. Upon successful execution of all tests, the Integration Graph must reach the `END` state.
- **Verification**: The LangGraph trace must show the sequence: `START -> git_merge_node -> (success) -> global_sandbox_node -> (pass) -> END`. The final state must reflect a successfully integrated repository.

### Scenario ID: Integration_Phase_02 - Conflict Resolution via 3-Way Diff
- **Priority**: High
- **Description**: Verify that the Integration Graph correctly detects a Git merge conflict and invokes the Master Integrator agent using the 3-Way Diff strategy to resolve it automatically. The system must attempt a merge and fail due to conflicting changes in the same file. It must route to the `master_integrator_node`, which extracts the Base, Local, and Remote versions of the file and constructs a prompt. The LLM (mocked in testing) provides a resolved code block. The system must apply this resolution, successfully complete the merge, and proceed to the Global Sandbox.
- **Verification**: The LangGraph trace must show the sequence: `START -> git_merge_node -> (conflict) -> master_integrator_node -> git_merge_node -> (success) -> global_sandbox_node -> (pass) -> END`. The prompt sent to the LLM must contain the `### Base`, `### Branch A`, and `### Branch B` sections.

### Scenario ID: Integration_Phase_03 - Post-Merge Semantic Failure Recovery
- **Priority**: Medium
- **Description**: Verify that the Integration Graph correctly handles a scenario where a merge is successful (no Git conflicts) or a Git conflict is resolved, but the resulting codebase fails semantic checks in the Global Sandbox (e.g., a function signature changed in one branch, breaking a call in another). The system must complete the merge and execute the Global Sandbox. The Sandbox must fail (simulated). The graph must then route the failure back to the `master_integrator_node` (or a dedicated integration-fix node) to resolve the semantic error.
- **Verification**: The LangGraph trace must show the sequence: `... -> global_sandbox_node -> (failed) -> master_integrator_node -> ... -> global_sandbox_node -> (pass) -> END`. The final state must successfully recover from the semantic failure.

## Behavior Definitions

### Feature: Automated 3-Way Diff Conflict Resolution
As a developer using an AI-native environment,
I want the system to automatically and intelligently resolve Git merge conflicts,
So that parallel development cycles can be integrated seamlessly without manual intervention.

**Background:**
Given the system has successfully completed at least two parallel Phase 2 (Coder Graph) cycles,
And the resulting feature branches are ready to be merged into the integration branch.

**Scenario: Successful clean merge of feature branches**
- Given the system starts Phase 3 (Integration Graph)
- And the integration branch is clean
- When the system attempts to merge Feature Branch A
- And there are no Git conflicts
- Then the system routes to the Global Sandbox
- And the Global Sandbox executes all linters and tests successfully
- Then the merge is finalized and the phase completes.

**Scenario: Automated resolution of a Git conflict using 3-Way Diff**
- Given the system is executing Phase 3 (Integration Graph)
- And the system attempts to merge Feature Branch B
- When Git detects a merge conflict in `utils.py`
- Then the system routes to the Master Integrator node
- And the Master Integrator extracts the Base, Local, and Remote versions of `utils.py`
- And the Master Integrator generates a unified, conflict-free version of `utils.py`
- And the system applies the resolution and commits the merge
- Then the system routes to the Global Sandbox
- And the Global Sandbox executes all linters and tests successfully
- Then the phase completes successfully.

**Scenario: Handling a semantic failure introduced during integration**
- Given the system has successfully merged Feature Branch C
- And the system is executing the Global Sandbox
- When the Global Sandbox detects a failing unit test due to an incompatible API change
- Then the system routes the failure logs back to the Master Integrator node
- And the Master Integrator analyzes the failure and applies a semantic fix
- And the system re-runs the Global Sandbox
- When the Global Sandbox tests pass
- Then the phase completes successfully.