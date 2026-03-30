# CYCLE 04 Specification: UAT Decoupling & QA Graph UAT

## Test Scenarios

### Scenario ID: 04-A (UAT Decoupling)
**Priority:** High
**Description:** The UAT use case must be able to execute independently of any specific coding cycle, acting on the integrated codebase.

### Scenario ID: 04-B (QA Routing on Failure)
**Priority:** High
**Description:** A failed UAT execution must correctly route to the QA Auditor with the necessary artifacts (e.g., screenshots).

## Behavior Definitions

### Scenario 04-A: Independent UAT Execution
```gherkin
GIVEN the Integration Phase has completed successfully
WHEN the UAT Use Case is executed
THEN it runs the E2E test suite against the unified workspace
AND it does not require a specific cycle ID to function
```

### Scenario 04-B: QA Routing
```gherkin
GIVEN the QA Graph is executing
WHEN uat_evaluate_node returns a status of "failed"
THEN the flow is directed to qa_auditor_node
AND the state contains the failure artifacts (e.g., screenshots or logs)

GIVEN the qa_session_node has implemented a fix
WHEN the node completes
THEN the flow is directed back to uat_evaluate_node to re-test
```