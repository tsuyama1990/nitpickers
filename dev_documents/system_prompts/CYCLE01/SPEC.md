# CYCLE 01: State Management & Phase 0/1 Setup

## Summary
The purpose of Cycle 01 is to establish the foundational data structures and state variables required to implement the new 5-Phase Architecture, focusing on Phase 0 (Init) and Phase 1 (Architect). This cycle introduces the control flags needed to manage the transition between the standard coding loops and the serial auditing and refactoring loops.

Specifically, it updates `CycleState` (and its sub-states) to track whether the code is currently in a refactoring pass (`is_refactoring`), the index of the serial auditor (`current_auditor_index`), and the number of audit attempts (`audit_attempt_count`).

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
*Target Project Secrets:* No new external APIs are introduced in this cycle. Existing keys (JULES_API_KEY, E2B_API_KEY, OPENROUTER_API_KEY) are sufficient.

### B. System Configurations (`docker-compose.yml`)
*Non-confidential configurations:* Ensure the Sidecar path variables are maintained. Do not modify `docker-compose.yml` for this specific cycle, as no new environmental overrides are needed for basic state modifications.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
*Mandate Mocking:* You MUST explicitly instruct the Coder that *all external API calls relying on the newly defined secrets in `.env.example` MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*.
While this cycle does not introduce new API calls, any state transitions triggering LLM invocations during tests MUST use mocked responses. The sandbox will not possess real API keys during autonomous evaluation. Attempting real network calls will crash the test suite and cause an infinite retry loop.

## System Architecture

The following file structure must be implemented or modified to support Phase 0 and Phase 1 state management:

```text
src/
├── **state.py**                  # Add missing state variables to CycleState/CommitteeState.
└── **state_validators.py**       # Add new validation logic for new variables.
```

## Design Architecture

This cycle modifies Pydantic-based schema models to robustly represent the workflow states.

1.  **`src/state.py` (`CommitteeState`)**:
    *   **Domain Concept**: Represents the internal state of the auditing committee, tracking which auditor is active and how many attempts have been made.
    *   **Invariants**:
        *   `current_auditor_index`: Integer, minimum 1 (defaults to 1). Tracks the current auditor (1 through 3).
        *   `audit_attempt_count`: Integer, minimum 0 (defaults to 0). Tracks rejections from the current auditor to prevent infinite loops.
        *   `is_refactoring`: Boolean (defaults to False). A flag to determine if the pipeline should route to the final critic after a successful sandbox run, rather than returning to the auditors.
    *   **Consumers**: LangGraph router functions (`route_auditor`, `route_sandbox_evaluate`).

2.  **`src/state_validators.py`**:
    *   **Domain Concept**: Centralizes validation logic for the Pydantic models.
    *   **Constraints**: Implement `validate_auditor_index` and `validate_audit_attempt_count` to ensure they never fall below their minimum values and handle type coercion if necessary.

## Implementation Approach

1.  **Update `CommitteeState`**: Open `src/state.py`. Within the `CommitteeState` class, add the following fields:
    *   `is_refactoring: bool = Field(default=False)`
    *   `current_auditor_index: int = Field(default=1, ge=1)` (Update if it exists, add if missing).
    *   `audit_attempt_count: int = Field(default=0, ge=0)` (Update if it exists, add if missing).
2.  **Update `CycleState` Properties**: In `src/state.py`, within `CycleState`, add `@property` and `@setter` definitions for `is_refactoring`, `current_auditor_index`, and `audit_attempt_count` that map directly to their corresponding `self.committee` attributes to ensure backward compatibility and easy access for legacy routers.
3.  **Implement Validators**: Open `src/state_validators.py`. Implement functions `validate_auditor_index(v: int) -> int` and `validate_audit_attempt_count(v: int) -> int`. Ensure these functions raise a `ValueError` if the value is less than 1 (for index) or 0 (for count).
4.  **Wire Validators to Model**: In `src/state.py` (`CommitteeState`), use `@field_validator` decorators to connect the fields to the functions in `state_validators.py`.

## Test Strategy

All tests must be executed without real LLM API calls, strictly using local, mocked dependencies.

**Unit Testing Approach (Min 300 words):**
We must test the structural integrity and validation rules of the `CommitteeState` and `CycleState` Pydantic models. Create tests in `tests/unit/test_state.py` (or equivalent).
*   **Test Default Values**: Instantiate `CycleState(cycle_id="test")`. Assert that `is_refactoring` is `False`, `current_auditor_index` is 1, and `audit_attempt_count` is 0.
*   **Test Property Setters**: Instantiate `CycleState`, assign `state.is_refactoring = True`. Assert that `state.committee.is_refactoring` is also `True`. Repeat for `current_auditor_index` and `audit_attempt_count`.
*   **Test Validation Boundaries**: Instantiate `CommitteeState` with invalid values (e.g., `current_auditor_index=0`, `audit_attempt_count=-1`). Use `pytest.raises(ValueError, match="...")` to verify that Pydantic correctly rejects these inputs based on the logic in `state_validators.py`. Ensure error messages are specific and descriptive.

**Integration Testing Approach (Min 300 words):**
While this cycle is primarily structural schema changes, we must ensure these state changes do not disrupt the initial instantiation of the Architect phase.
*   **Test Graph State Injection**: Create a dummy LangGraph execution flow (or mock the existing `build_architect_graph`). Initialize the flow with a `CycleState`. Transition the state through a dummy node that updates `audit_attempt_count` to `2` and `is_refactoring` to `True`. Verify that the final state output by the graph retains these specific mutated values and does not lose them during serialization/deserialization checkpoints. Mock any `MemorySaver` dependencies to use a local, ephemeral sqlite/in-memory store.