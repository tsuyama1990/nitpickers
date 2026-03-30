# CYCLE02 UAT: Integration & UAT Automation (Phases 3 & 4)

## Test Scenarios

These scenarios are strictly constructed to validate the Phase 3 (Integration Graph) and Phase 4 (QA Graph) capabilities of the 5-Phase Architecture. They focus intensely on resolving complex Git merge conflicts via the new 3-Way Diff analysis and executing isolated, holistic User Acceptance Tests post-integration. The success of these tests guarantees that the system can autonomously handle the messy reality of multi-branch development without human intervention. These tests must be entirely runnable within the `tutorials/UAT_AND_TUTORIAL.py` Marimo notebook, serving as both continuous integration checks and interactive developer documentation.

### Scenario ID: UAT-C02-001
*   **Priority**: High
*   **Title**: 3-Way Diff Conflict Resolution (Phase 3)
*   **Description**: This scenario is the crucible for the entire Integration Phase. It simulates a highly realistic situation where two parallel Coder cycles (e.g., Cycle A adding a new feature and Cycle B refactoring a core module) modify the exact same file concurrently, creating a standard, textual Git merge conflict. The Integration Graph must detect this conflict, intercept the failure, extract the Base, Local (Branch A), and Remote (Branch B) code blocks using the `ConflictManager`, and correctly format a prompt for the `master_integrator_node` to resolve it. Finally, it must succeed in the subsequent merge attempt and pass the global sandbox validation. The critical element here is proving that the LLM is provided with the structured 3-Way Diff context, not just a raw file full of `<<<<<<< HEAD` markers, ensuring a semantically correct resolution rather than a naive string replacement.
*   **Execution Strategy**: To guarantee stability in CI environments, this test must be executed in "Mock Mode". The Marimo notebook will program the `git_merge_node` to return a `conflict` status initially, simulating a failed `git merge` command. We must then provide mocked strings for the `subprocess.run` calls simulating `git show :1`, `:2`, and `:3` to the `ConflictManager`. The `master_integrator_node` mock should be programmed to return a synthesized, conflict-free "resolved" code block. Upon the second pass, the `git_merge_node` mock should return `success`.
*   **Validation Point**: The primary assertion is a strict examination of the LangGraph state trace. The trace must definitively show the exact path: `git_merge_node` -> `master_integrator_node` -> `git_merge_node` (retry) -> `global_sandbox_node` -> `END`. Crucially, the test must explicitly assert that the generated LLM prompt stored within the `IntegrationState` contains the distinct Markdown sections "Base", "Branch A", and "Branch B", proving the 3-Way Diff logic assembled the package correctly before invoking the Integrator agent.

### Scenario ID: UAT-C02-002
*   **Priority**: High
*   **Title**: Isolated QA Execution and Remediation (Phase 4)
*   **Description**: This scenario ensures that the QA Graph executes strictly *after* successful integration and operates entirely independently of the Coder Phase loops. It tests the automated failure and remediation loop where an initial UAT evaluation (e.g., a simulated Playwright End-to-End test running against the integrated application) fails due to an integration bug not caught by the unit tests. The workflow must correctly capture the failure, route to the `qa_auditor` to analyze the failure (using simulated logs or screenshots), and then route to the `qa_session` to apply a targeted fix. Finally, it must re-execute the UAT evaluation, leading to a final successful validation. This proves the system can self-heal functional defects in the fully integrated product.
*   **Execution Strategy**: In "Mock Mode", the Marimo notebook will program the initial `uat_evaluate` node to return a "failed" status and populate the `QaState` with mock error logs mimicking a Playwright exception. The subsequent `qa_auditor` mock will return a diagnostic string. The `qa_session` node mock will simulate applying a code fix to the integration branch. The crucial step is programming the second invocation of `uat_evaluate` to return a "passed" status, simulating a successful remediation.
*   **Validation Point**: The primary assertion is the LangGraph state trace. The trace must definitively show the sequence: `uat_evaluate` (Fail) -> `qa_auditor` -> `qa_session` -> `uat_evaluate` (Pass) -> `END`. The test must explicitly assert that this graph operates entirely independently of any `CycleState` objects, proving the architectural boundary between Phase 2 (Coding) and Phase 4 (QA) is strictly maintained.

### Scenario ID: UAT-C02-003
*   **Priority**: Medium
*   **Title**: Global Sandbox Failure and Regression Fix (Phase 3)
*   **Description**: This scenario tests a subtle but critical failure mode: the situation where a standard Git merge is entirely successful (meaning there are no textual Git conflicts to resolve), but the combined code introduces a logical regression or structural issue that is caught by the `global_sandbox_node` (e.g., an integration test fails because Branch A changed an API signature that Branch B still relies upon). The system must detect this semantic failure, route back to the `master_integrator_node` to intelligently fix the regression based on the test logs, before proceeding. This ensures that a successful textual merge does not equate to a successful integration if the resulting codebase is broken.
*   **Execution Strategy**: In "Mock Mode", the test will program the `git_merge_node` to return "success" on its first pass. However, the `global_sandbox_node` will be mocked to return a "failed" status, simulating a broken build or failing test suite. The `master_integrator_node` mock must then be invoked to apply a simulated fix, and the state must be updated. The subsequent run of the `global_sandbox_node` must be mocked to return "passed".
*   **Validation Point**: The state trace must definitively show the sequence: `git_merge_node` (Success) -> `global_sandbox_node` (Fail) -> `master_integrator_node` -> `git_merge_node` (Retry, Success) -> `global_sandbox_node` (Pass) -> `END`. The test must assert that the `IntegrationState` correctly tracks the failure reason and passes the sandbox logs to the Integrator agent, enabling a semantic repair of the integrated codebase.

## Behavior Definitions (Gherkin)

The following Gherkin definitions provide a human-readable, executable specification for the core behaviors expected from the newly implemented Integration and QA Graphs. They serve as the definitive contract for the integration logic, ensuring that all edge cases regarding 3-Way Diff resolution, automated UAT execution, and remediation loops are explicitly defined and testable by the development team. These definitions form the basis for the automated tests implemented in the Marimo notebook, guaranteeing that the final stages of the 5-Phase Architecture function exactly as designed.

**Feature: Phase 3 Integration and Phase 4 Final Quality Assurance**

As a System Architect managing an autonomous software factory,
I want the Integration Graph to handle complex Git conflicts using a 3-Way Diff approach, and the QA Graph to enforce automated End-to-End testing,
So that I can ensure parallel feature development merges cleanly and the final product meets user requirements without manual intervention.

**Scenario: Resolving a Textual Git Conflict via 3-Way Diff Analysis**
*   **GIVEN** the system initializes an `IntegrationState` representing two divergent feature branches (Branch A and Branch B) ready to be merged into the `int` branch
*   **WHEN** the orchestrator triggers the execution of the `_create_integration_graph`
*   **AND** the initial `git_merge_node` attempts a standard `git merge` command, but the command fails due to a textual conflict
*   **THEN** the routing logic must detect the conflict status and transition the workflow to the `master_integrator_node`
*   **AND** the `ConflictManager` must successfully extract the Base common ancestor file version
*   **AND** the `ConflictManager` must successfully extract the Local (Branch A) file version
*   **AND** the `ConflictManager` must successfully extract the Remote (Branch B) file version
*   **AND** the `ConflictManager` must construct a comprehensive 3-Way Diff prompt, explicitly labeling these three distinct code blocks for the Integrator LLM
*   **WHEN** the `master_integrator_node` processes the prompt and provides a completely resolved, unified file
*   **THEN** the workflow must loop back and retry the `git merge` command, which now completes successfully
*   **AND** the routing logic must transition the workflow to the `global_sandbox_node` for structural verification
*   **AND** upon structural success, the workflow must successfully complete Phase 3 and reach the terminal `END` state.

**Scenario: Automated QA Remediation Loop for End-to-End Failures**
*   **GIVEN** the system has successfully completed Phase 3 Integration, resulting in a unified codebase, and initializes a valid `QaState`
*   **WHEN** the orchestrator triggers the execution of the `_create_qa_graph`
*   **AND** the initial `uat_evaluate` node executes the final Playwright E2E test suite against the integrated application
*   **AND** a critical UAT test fails, generating comprehensive error logs and a simulated screenshot
*   **THEN** the routing logic must transition the workflow to the `qa_auditor`
*   **AND** the `qa_auditor` must process the test logs and screenshot to diagnose the root cause of the UI failure
*   **AND** the routing logic must transition the workflow to the `qa_session` to apply the targeted fix to the integration branch
*   **WHEN** the `qa_session` completes the code modification and updates the state
*   **THEN** the workflow must loop back and re-execute the `uat_evaluate` node, running the full E2E test suite again
*   **AND** upon all tests passing, the workflow must successfully complete Phase 4 and reach the terminal `END` state, marking the entire 5-Phase pipeline as finished.