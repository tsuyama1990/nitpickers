# CYCLE 02 Specification: Routers and Node logic UAT

## Test Scenarios

### Scenario ID: 02-A (Sandbox Router)
**Priority:** High
**Description:** The sandbox router must correctly differentiate between a normal pass (to auditor) and a post-refactoring pass (to final critic).

### Scenario ID: 02-B (Auditor Serial Loop)
**Priority:** High
**Description:** The auditor router must correctly increment the index and transition to "pass_all" only when the index exceeds 3.

### Scenario ID: 02-C (Refactoring Flag Toggle)
**Priority:** High
**Description:** After passing all auditors, the refactor node must set `is_refactoring` to True before re-evaluating the sandbox.

## Behavior Definitions

### Scenario 02-A: Sandbox Evaluator Routing
```gherkin
GIVEN the Sandbox Evaluator completes successfully
WHEN is_refactoring is False
THEN route_sandbox_evaluate returns 'auditor'

GIVEN the Sandbox Evaluator completes successfully
WHEN is_refactoring is True
THEN route_sandbox_evaluate returns 'final_critic'
```

### Scenario 02-B: Auditor Routing
```gherkin
GIVEN the Auditor Node returns Approve
WHEN current_auditor_index is 2
THEN route_auditor increments the index to 3
AND returns 'next_auditor'

GIVEN the Auditor Node returns Approve
WHEN current_auditor_index is 3
THEN route_auditor increments the index to 4
AND returns 'pass_all'
```

### Scenario 02-C: Refactor Node Effect
```gherkin
GIVEN the Refactor Node is executed
WHEN the state transitions out of the node
THEN is_refactoring must be True
```