# CYCLE 04: Phase 4 UAT & QA Graph UAT

## Test Scenarios

### Scenario ID: UAT-04-01 (Priority: High)
**Description:** Verify the `_create_qa_graph` operates entirely independently of individual Coder phase cycles, successfully diagnosing and fixing a simulated Playwright End-to-End test failure using multimodal vision analysis.
**Setup:** A Marimo notebook executing the `_create_qa_graph` using `pytest.MonkeyPatch` to simulate deterministic node responses and a predefined `CycleState` representing the entire global session.
**Execution (Mock Mode):**
*   Initialize a global `CycleState(cycle_id="qa-global")`.
*   Execute the compiled `qa_graph`.
*   Mock `uat_evaluate` to return a `FlowStatus.UAT_FAILED` status with simulated error logs and a base64 dummy screenshot artifact.
*   Mock `qa_auditor` to accept the multimodal artifact and return a structured JSON fix plan.
*   Mock `qa_session` to apply the fix plan.
*   Mock `qa_regression_sandbox_node` to pass local unit tests.
*   Mock `uat_evaluate` to return `FlowStatus.COMPLETED` on the second iteration.
**Verification:**
*   The `uat_evaluate_node` must have been visited twice.
*   The `qa_auditor`, `qa_session`, and `qa_regression_sandbox_node` must have been visited exactly once.
*   The pipeline must terminate successfully at `END` via the `ux_auditor` path.

### Scenario ID: UAT-04-02 (Priority: Medium)
**Description:** Verify that `uat_usecase.py` has been fully decoupled and does not crash when executed with a state lacking granular feature implementation details (e.g., missing specific file code operations from a Coder graph).
**Setup:** A Marimo notebook block directly instantiating the modified `UatUsecase` class with a minimal `CycleState` and executing its evaluation logic.
**Execution (Mock Mode):**
*   Instantiate `UatUsecase` with `CycleState(cycle_id="standalone-qa")`.
*   Invoke the core evaluation method (mocking the underlying `ProcessRunner` to simulate Playwright passing).
**Verification:**
*   The method must execute to completion without throwing `KeyError` or `AttributeError` exceptions related to missing Coder-specific state variables.

## Behavior Definitions

**Feature:** Independent UAT & QA Execution
**As a** system orchestrator,
**I want** the End-to-End User Acceptance Testing phase to operate as an independent graph process after the entire system has been integrated,
**So that** I can ensure all feature cycles are validated together under real-world conditions without tightly coupling tests to individual cycle implementations.

**Scenario:** Successful full-system UAT execution
**GIVEN** an active global QA session following a successful Integration Phase
**WHEN** the pipeline routes to the `uat_evaluate` node
**AND** the Playwright tests pass cleanly
**THEN** the pipeline must route immediately to the `ux_auditor` or `END`
**AND** the system must bypass the diagnostic remediation loop entirely.

**Scenario:** UAT failure triggers multimodal QA remediation loop
**GIVEN** an active global QA session following Integration
**WHEN** the `uat_evaluate` node encounters a UI failure
**THEN** a screenshot and error log must be captured and passed to the `qa_auditor`
**AND** the pipeline must route the resulting fix plan through the `qa_session` and `qa_regression_sandbox_node`
**AND** upon successfully passing local regressions, the pipeline must re-evaluate the full UAT suite.