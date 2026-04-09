<thought>
Let's see what needs to be done.
The task specifies that I should modify `src/state.py` to add `is_refactoring`, `current_auditor_index` and `audit_attempt_count`. But looking at `src/state.py`, they are already present:
```python
class CommitteeState(BaseModel):
    current_auditor_index: int = Field(default=1, ge=1)
    current_auditor_review_count: int = Field(default=1, ge=1)
    iteration_count: int = Field(default=0, ge=0)
    is_refactoring: bool = Field(default=False)
    audit_attempt_count: int = Field(default=0, ge=0)
```

However, I need to add properties to `CycleState` for `is_refactoring` and `audit_attempt_count` for backward compatibility. Looking at `src/state.py`, `CycleState` does NOT have `@property` accessors for `is_refactoring` and `audit_attempt_count`, though it has for `current_auditor_index`, `current_auditor_review_count`, `iteration_count`. So I need to add those to `CycleState`.

For `src/nodes/routers.py`:
`route_sandbox_evaluate` already exists:
```python
    if status == FlowStatus.READY_FOR_AUDIT:
        if state.committee.is_refactoring:
            return "final_critic"
        return "auditor"
```
Wait, the router logic might be already there, let's look at `route_auditor` in `src/nodes/routers.py`.
```python
def route_auditor(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == FlowStatus.REQUIRES_PIVOT:
        state.committee.audit_attempt_count += 1
        return "requires_pivot"

    # Use explicit audit_result field from state.audit based on trace inspection
    is_approved = False
    if state.audit.audit_result is not None:
        is_approved = state.audit.audit_result.is_approved

    if not is_approved:
        state.committee.audit_attempt_count += 1
        if state.committee.audit_attempt_count > settings.max_audit_retries:
            return "requires_pivot"
        return "reject"

    # Reset attempt count on pass
    state.committee.audit_attempt_count = 0
    state.committee.current_auditor_index += 1

    if state.committee.current_auditor_index > settings.NUM_AUDITORS:
        return "pass_all"

    return "next_auditor"
```
It already looks quite identical to the spec.
Wait! What about the requirement: "Crucial Enforcement: Ensure the LLM interaction within refactor_node uses pydantic-ai or similar litellm capabilities..."
And the requirement says "Phase 2: Test Driven Development (TDD) Write tests that target your new Schemas and Interface definitions. Unit Tests... Integration Tests... UAT Verification..."

Let's read the `SPEC.md` again.
1. `src/state.py`:
- `CommitteeState` add `is_refactoring`, `audit_attempt_count`. They are already there.
- Update `CycleState` properties to provide getter/setter access to these new fields.
2. `src/nodes/routers.py`:
- Implement `route_sandbox_evaluate`, `route_auditor`, `route_final_critic`. They are already mostly there!
3. `src/graph.py`:
- Rewire `_create_coder_graph`.

Let's verify what's actually there.
The environment must be existing code that partly implemented the requirements, or maybe I need to write missing unit/integration tests because the prompt specifically mentioned: "CRITICAL TDD ENFORCEMENT: You are in the 'RED' phase of Test-Driven Development. You MUST write FAILING TESTS ONLY. Do NOT write or modify any implementation code yet. Your goal is to produce a test that fails against the current implementation to prove the bug exists or the feature is missing."

Wait! The user prompt says:
"CRITICAL TDD ENFORCEMENT:
You are in the 'RED' phase of Test-Driven Development. You MUST write FAILING TESTS ONLY. Do NOT write or modify any implementation code yet. Your goal is to produce a test that fails against the current implementation to prove the bug exists or the feature is missing."

Ah! I only need to write **FAILING TESTS ONLY**. I should NOT modify `src/state.py` or `src/nodes/routers.py` or `src/graph.py` yet! I need to write tests that FAIL!
Wait, but if I'm testing `is_refactoring` and `audit_attempt_count` on `CycleState` property accessors, they will fail because they don't exist yet!

So the plan is:
1. Write failing unit tests in `tests/unit/test_state.py` for `is_refactoring` and `audit_attempt_count` properties on `CycleState`.
2. Write failing unit tests in `tests/nodes/test_routers.py` for `route_sandbox_evaluate`, `route_auditor`, and `route_final_critic` (though some might already pass).
3. Write a failing integration test in `tests/e2e/test_coder_graph.py` to test the rewired graph (e.g. testing rejection loop, pass all).
4. Run tests to ensure they fail.
5. Provide pre-commit steps.

Let's look at `tests/unit/test_state.py`
