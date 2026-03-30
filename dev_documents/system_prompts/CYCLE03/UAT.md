# CYCLE03 UAT Plan

## Test Scenarios

### Scenario 1: UAT Evaluation After Integration (Priority: High)
This scenario ensures that the UAT Phase is correctly decoupled from the Coder Phase and exclusively triggered after a successful Phase 3 (Integration Graph) execution.

### Scenario 2: UAT Self-Healing Loop (Priority: High)
This scenario validates the automated remediation process when a User Acceptance Test fails, ensuring the `qa_auditor` and `qa_session` correctly loop back to `uat_evaluate` until the issue is resolved.

### Behavior Definitions

**Scenario 1: UAT Evaluation After Integration**

GIVEN a successful execution of the Phase 3 `_create_integration_graph`
AND the `global_sandbox_node` returns a "pass" status
WHEN the Phase 4 `_create_qa_graph` is initiated
THEN the `uat_evaluate` node should be executed
AND the UAT tests should execute against the fully integrated codebase

**Scenario 2: UAT Self-Healing Loop**

GIVEN the workflow has entered Phase 4
AND the `uat_evaluate` node executes and encounters a failed E2E test, capturing a Playwright artifact
WHEN the workflow routes to the `qa_auditor` node
THEN the `qa_auditor` should ingest the artifact and return a structured JSON fix plan
AND the workflow should route to the `qa_session` node to apply the fix
AND the workflow should loop back to `uat_evaluate` and successfully pass
