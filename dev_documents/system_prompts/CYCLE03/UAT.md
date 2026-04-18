# CYCLE03 UAT: Orchestration & QA Graph Validation

## Test Scenarios

### Scenario ID: Pipeline_Orchestration_01 - Full 5-Phase Execution
- **Priority**: High
- **Description**: Verify that the CLI successfully orchestrates a complete run of all five phases for a multi-cycle project. This is the ultimate end-to-end integration test of the system architecture. The user initiates the `run-pipeline` (or equivalent) command. The system must concurrently execute two independent Coder Phase (Phase 2) graphs (e.g., `CYCLE01` and `CYCLE02`). It must wait for both to reach the `END` state successfully. It must then transition to Phase 3, executing the Integration Graph to merge both cycles. Finally, upon successful integration, it must transition to Phase 4, executing the QA Graph (UAT evaluation). The entire process must complete without manual intervention and exit with a zero status code.
- **Verification**: The console output must clearly log the transition between phases: `Starting Phase 2 (Parallel)` -> `Awaiting Cycle 01 and Cycle 02` -> `Starting Phase 3 (Integration)` -> `Starting Phase 4 (UAT)`. The final system state must show all UAT scenarios passed against the integrated branch.

### Scenario ID: Pipeline_Orchestration_02 - Fail-Fast on Coder Phase Error
- **Priority**: High
- **Description**: Verify that the orchestrator correctly halts the entire pipeline if a single parallel Coder Phase (Phase 2) cycle fails catastrophically (e.g., exceeds retry limits, unrecoverable syntax error). The user initiates the pipeline with two cycles. `CYCLE01` is mocked to succeed, but `CYCLE02` is mocked to fail (e.g., reaching a designated error node or throwing an exception). The orchestrator must detect the failure of `CYCLE02`, cancel any pending operations, log the error clearly, and **strictly prevent** the execution of Phase 3 (Integration) and Phase 4 (UAT).
- **Verification**: The CLI must exit with a non-zero status code. The console output must indicate which cycle failed. The log must *not* contain any entries indicating that Phase 3 or Phase 4 was initiated.

### Scenario ID: QA_Graph_01 - Automated UAT Remediation Loop
- **Priority**: Medium
- **Description**: Verify that the isolated QA Graph (Phase 4) correctly handles a failing UAT scenario by invoking the Vision LLM and the QA Session agent to implement a fix. The user executes the pipeline up to Phase 4. A pre-configured Playwright UAT test is designed to fail intentionally against the integrated code (e.g., a missing DOM element). The QA Graph must catch the failure, capture the Playwright screenshot and DOM snapshot, send these artifacts to the `qa_auditor` (OpenRouter Vision LLM), receive a JSON fix plan, route to the `qa_session` (Coder LLM) to apply the fix, and loop back to re-evaluate the UAT. The second evaluation must pass.
- **Verification**: The LangGraph trace for Phase 4 must show the sequence: `uat_evaluate -> (failed) -> qa_auditor -> qa_session -> uat_evaluate -> (pass) -> END`. The final UAT status must be successful.

## Behavior Definitions

### Feature: Multi-Phase Orchestration and E2E Testing
As a technical lead using an AI-native environment,
I want the system to manage parallel development and sequential integration automatically,
So that I can trust the final E2E test results are based on the fully integrated codebase.

**Background:**
Given the system has been initialized with a valid `ALL_SPEC.md` defining `CYCLE01` and `CYCLE02`,
And the user executes the full pipeline command via CLI.

**Scenario: Successful parallel execution and sequential integration**
- Given the orchestrator starts the pipeline
- When the system launches Phase 2 for `CYCLE01` and `CYCLE02` concurrently
- And `CYCLE01` completes successfully
- And `CYCLE02` completes successfully
- Then the system waits at the Phase Barrier
- And the system transitions to Phase 3 (Integration Graph)
- When the Integration Graph completes successfully
- Then the system transitions to Phase 4 (QA Graph)
- When the QA Graph executes all Playwright UAT scenarios successfully
- Then the entire pipeline completes with a success status.

**Scenario: Pipeline fail-fast mechanism triggers on parallel failure**
- Given the orchestrator starts the pipeline
- When the system launches Phase 2 for `CYCLE01` and `CYCLE02` concurrently
- And `CYCLE01` encounters an unrecoverable logic error and fails
- Then the orchestrator immediately detects the failure
- And the orchestrator cancels or ignores the completion of `CYCLE02`
- And the system halts execution with a non-zero exit code
- And the system does NOT execute Phase 3 (Integration Graph) or Phase 4 (QA Graph).

**Scenario: Automated remediation of UI failures in Phase 4**
- Given the system has successfully completed Phase 3 (Integration Graph)
- And the system transitions to Phase 4 (QA Graph)
- When the system executes the E2E UAT scenarios
- And a Playwright test fails due to a missing button
- Then the system captures a screenshot and DOM snapshot of the failure
- And the system routes the artifacts to the QA Auditor (Vision LLM)
- And the QA Auditor generates a fix plan for the missing button
- And the QA Session applies the code changes
- And the system re-runs the UAT scenarios
- When the Playwright tests pass successfully
- Then Phase 4 completes with a success status.
