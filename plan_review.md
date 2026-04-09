<thought>
The requirements state:
"CRITICAL TDD ENFORCEMENT:
You are in the 'RED' phase of Test-Driven Development. You MUST write FAILING TESTS ONLY. Do NOT write or modify any implementation code yet. Your goal is to produce a test that fails against the current implementation to prove the bug exists or the feature is missing."

According to the SPEC:
1. `tests/unit/test_state.py`:
- Test Pydantic field validators enforce constraints (e.g. `audit_attempt_count` cannot be negative)
- Test backward compatibility properties on `CycleState` (`is_refactoring`, `audit_attempt_count`, `current_auditor_index` etc) - meaning we can do `state.is_refactoring = True` and it changes `state.committee.is_refactoring`.

2. `tests/nodes/test_routers.py`:
- Test `route_sandbox_evaluate` (sandbox failed -> "failed", is_refactoring -> "final_critic", else -> "auditor"). Note: Some of this logic may already pass, but write tests anyway.
- Test `route_auditor` (Reject -> increment attempt, route to `reject`, Approve -> increment index, next_auditor / pass_all).
- Test `route_final_critic` (Approve -> "approve", Reject -> "reject").

3. `tests/e2e/test_coder_graph.py` (Integration Testing):
- Happy Path: start -> test_coder_node -> ... -> pass final critic -> END
- Rejection Loop: auditor rejects multiple times -> routes back to Coder -> audit_attempt_count reflects iterations.

So I will:
1. Write these tests.
2. Ensure they fail (because some properties on CycleState don't exist, e.g., `state.is_refactoring`, and the `test_coder_graph` might fail to traverse if mocked incorrectly).
3. Do NOT modify any implementation code.
