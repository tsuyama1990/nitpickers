# CYCLE 02: Phase 2 Coder Graph UAT

## Test Scenarios

### Scenario ID: UAT-02-01 (Priority: High)
**Description:** Verify the serial auditing loop correctly iterates through all three auditors before triggering the refactoring phase.
**Setup:** A Marimo notebook executing the `_create_coder_graph` using `pytest.MonkeyPatch` to simulate deterministic node responses. The initial code implementation must trigger an approval from all auditors.
**Execution (Mock Mode):**
*   Initialize `CycleState` for a standard implementation task.
*   Execute the compiled `coder_graph`.
*   Mock `coder_session`, `sandbox_evaluate`, and `self_critic` to return `status="passed"`.
*   Mock `auditor_node` to consistently return an "approve" `AuditResult`.
*   Mock `refactor_node` to set `state.is_refactoring = True`.
*   Mock `final_critic_node` to return an "approve" result.
**Verification:**
*   The `current_auditor_index` must have incremented from 1 to 3, meaning the `auditor_node` was visited exactly three times sequentially.
*   The `refactor_node` must have been visited exactly once.
*   The `final_critic_node` must have been visited exactly once, terminating the graph successfully.

### Scenario ID: UAT-02-02 (Priority: Medium)
**Description:** Verify that an auditor rejection routes the execution back to the Coder for remediation, preventing premature progression.
**Setup:** A Marimo notebook executing the `_create_coder_graph` with a mock auditor designed to reject the first iteration and approve the second.
**Execution (Mock Mode):**
*   Initialize `CycleState`.
*   Execute the compiled `coder_graph`.
*   Mock `sandbox_evaluate` to return "passed".
*   Mock `auditor_node` to return a "reject" `AuditResult` on the first invocation (with `current_auditor_index=1`), and an "approve" result on subsequent invocations.
**Verification:**
*   The execution trace must show a loop from `auditor_node` -> `coder_session` (or remediation node) -> `sandbox_evaluate` -> `auditor_node`.
*   The `audit_attempt_count` must register the rejection.
*   The graph must eventually succeed after the simulated remediation.

## Behavior Definitions

**Feature:** Serial Auditing Loop Routing
**As a** system orchestrator,
**I want** to route code through a sequential series of distinct LLM auditor roles,
**So that** I can enforce strict, layered code quality checks before allowing a PR to be finalized.

**Scenario:** Successful complete auditing sequence
**GIVEN** an active coding cycle that has passed initial sandbox evaluation
**WHEN** the code is submitted to the first auditor
**AND** all three auditors sequentially approve the implementation
**THEN** the pipeline must route the code to the refactoring node
**AND** subsequently to the final critic node, bypassing further auditor checks via the `is_refactoring` flag.

**Scenario:** Auditor rejection triggers remediation loop
**GIVEN** an active coding cycle in the auditing phase
**WHEN** the second auditor detects a defect and returns a rejection payload
**THEN** the pipeline must immediately route the code back to the coder node
**AND** the `audit_attempt_count` for the current auditor must increment
**AND** the `current_auditor_index` must remain at 2, awaiting a successful fix.