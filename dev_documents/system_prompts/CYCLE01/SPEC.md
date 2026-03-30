# CYCLE 01 Specification: Core State & Scenario Definition

## Summary
The goal of CYCLE 01 is to lay the foundational domain models for the 5-Phase Architecture. This involves extending the existing LangGraph state structures in `src/state.py` to support explicit routing loops (e.g., tracking the auditor count and refactoring phase). No complex orchestration or agent logic is modified in this cycle; the focus is entirely on robust data structures and type safety, ensuring backward compatibility with existing components.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
- No new external APIs or secret dependencies are introduced in this cycle.

### B. System Configurations (`docker-compose.yml`)
- No structural changes to `docker-compose.yml` are required for core state modifications.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
- While no direct external API calls are made from the models themselves, ensure any unit tests verifying model behavior in mocked workflows strictly mock `E2B_API_KEY` and any OpenRouter/Jules clients. The Sandbox will not possess real API keys during automated model validations.

## System Architecture

The following files will be created or modified to establish the new state contracts:

```text
src/
├── **state.py**                # Core Domain Pydantic Models
tests/
├── **test_state.py**           # Unit tests for CycleState and IntegrationState
```

## Design Architecture

### `src/state.py`
This system is fully designed by Pydantic-based schema.

1.  **`CycleState` (Extension):**
    -   **Concept:** Represents the state of a single parallel feature implementation cycle (Phase 2).
    -   **New Fields:**
        -   `is_refactoring: bool = False`: Determines if the current cycle is in the initial implementation phase or the post-audit polishing phase.
        -   `current_auditor_index: int = 1`: Tracks the serial auditor chain (typically 1 to 3).
        -   `audit_attempt_count: int = 0`: Counts the number of rejections from a specific auditor to prevent infinite loops. Max 2 retries per auditor.
    -   **Constraints/Invariants:** `current_auditor_index` must be > 0. `audit_attempt_count` must be >= 0.

2.  **`IntegrationState` (New):**
    -   **Concept:** Represents the state of Phase 3 (3-Way Diff Integration).
    -   **Fields:**
        -   `branches_to_merge: list[str]`: A list of branch names (e.g., `["cycle-01", "cycle-02"]`) ready for integration.
        -   `conflict_files: list[str]`: Paths to files currently experiencing merge conflicts.
        -   `global_sandbox_status: str`: Status of the final, global test run.

## Implementation Approach

1.  **Modify `CycleState`:**
    -   Open `src/state.py`.
    -   Add `is_refactoring`, `current_auditor_index`, and `audit_attempt_count` to the `CycleState` Pydantic model with default values.

2.  **Create `IntegrationState`:**
    -   In `src/state.py`, create a new Pydantic model `IntegrationState` inheriting from the base schema configuration.
    -   Add the required fields (`branches_to_merge`, `conflict_files`, `global_sandbox_status`).

3.  **Update Validation:**
    -   Ensure existing schemas remain valid and backward-compatible.

## Test Strategy

### Unit Testing Approach
-   **File:** `tests/test_state.py`
-   **Objectives:**
    -   Verify `CycleState` initializes with default values (`is_refactoring=False`, `current_auditor_index=1`, `audit_attempt_count=0`).
    -   Verify that valid states can be instantiated without triggering Pydantic `ValidationError`s.
    -   Verify `IntegrationState` instantiation and type validation for list properties.

### Integration Testing Approach
-   No deep integration tests are needed for purely structural Pydantic models in this cycle, but ensure that any existing graph tests in the test suite still pass successfully given the additive defaults.