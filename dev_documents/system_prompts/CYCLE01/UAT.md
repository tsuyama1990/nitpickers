# CYCLE01 UAT Plan

## Test Scenarios

### Scenario 1: Initial Implementation Audit Sequence (Priority: High)
The primary objective of this scenario is to validate the core routing logic of the Coder Graph during the initial implementation phase, confirming that the system correctly iterates through the sequential Auditor chain when the code passes the local sandbox evaluation but requires further refinement.

### Scenario 2: Refactoring Phase Routing (Priority: High)
This scenario ensures that the system correctly bypasses the standard Auditor chain and routes directly to the Final Critic node once the initial implementation has been approved by all standard auditors and the `is_refactoring` flag has been toggled.

### Behavior Definitions

**Scenario 1: Initial Implementation Audit Sequence**

GIVEN a `CycleState` with `sandbox_status` equal to "pass"
AND the `is_refactoring` flag is set to `False`
WHEN the `route_sandbox_evaluate` function is invoked
THEN it should return the routing literal "auditor"

GIVEN the workflow has entered the Auditor node sequence
AND the `current_auditor_index` is 1
WHEN the current Auditor returns an "approve" result
THEN the `route_auditor` function should increment `current_auditor_index` to 2
AND it should return the routing literal "next_auditor"

GIVEN the workflow is in the Auditor node sequence
AND the `current_auditor_index` is 3 (the final standard auditor)
WHEN the current Auditor returns an "approve" result
THEN the `route_auditor` function should recognize the maximum index has been reached
AND it should return the routing literal "pass_all"

GIVEN the workflow is in the Auditor node sequence
WHEN the current Auditor returns a "reject" result
THEN the `route_auditor` function should increment the `audit_attempt_count`
AND it should return the routing literal "reject" to route the workflow back to the Coder node for remediation

**Scenario 2: Refactoring Phase Routing**

GIVEN a `CycleState` where the `is_refactoring` flag has been toggled to `True`
AND the `sandbox_status` is equal to "pass"
WHEN the `route_sandbox_evaluate` function is invoked
THEN it should return the routing literal "final_critic", bypassing the standard Auditor sequence

GIVEN the workflow has reached the Final Critic node
WHEN the self-evaluation result is "reject"
THEN the `route_final_critic` function should return the routing literal "reject" to route back to the Coder node

GIVEN the workflow has reached the Final Critic node
WHEN the self-evaluation result is "approve"
THEN the `route_final_critic` function should return the routing literal "approve" to signal the successful completion of the cycle
