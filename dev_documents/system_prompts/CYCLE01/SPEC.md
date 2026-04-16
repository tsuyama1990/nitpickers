# CYCLE01: State Management Updates

## Summary
CYCLE01 focuses on modifying the core state definition (`src/state.py`) of the LangGraph workflow to support the new 5-Phase architecture. Specifically, we are injecting control flags and tracking indices to enable deterministic routing through the Coder Graph's serial audit loop and self-healing refactoring steps.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
- No new external API secrets are strictly required for this specific state modification cycle.

### B. System Configurations (`docker-compose.yml`)
- No new environment variables are needed for the container environment.

### C. Sandbox Resilience
- **Mandate Mocking**: Since this cycle deals purely with Pydantic/TypedDict state modifications, any associated state transition tests MUST mock external agent dependencies to avoid unintended API calls during local validation.

## System Architecture

Modifications are confined to the state definition file.

```text
nitpickers/
└── src/
    └── **state.py**
```

## Design Architecture

The `CycleState` schema (whether TypedDict or Pydantic model) acts as the data payload passed between nodes in the LangGraph.

- **`is_refactoring` (bool)**:
  - Default: `False`
  - Invariant: Toggled to `True` only after the audit sequence passes and the system enters the refactoring node. Determines if the graph routes to the final critic or loops back to auditors.
- **`current_auditor_index` (int)**:
  - Default: `1`
  - Invariant: Tracks progression through the serial auditor sequence (1 through 3). Cannot exceed 3.
- **`audit_attempt_count` (int)**:
  - Default: `0`
  - Invariant: Tracks failure retries for the current auditor. Prevents infinite loops by setting a hard cap (e.g., max 2 attempts). Resets when moving to a new auditor index.

## Implementation Approach

1.  Open `src/state.py`.
2.  Locate the `CycleState` class definition.
3.  Add the `is_refactoring` field with a default of `False`.
4.  Add the `current_auditor_index` field with a default of `1`.
5.  Add the `audit_attempt_count` field with a default of `0`.
6.  Ensure that if `CycleState` utilizes Pydantic, proper `Field` defaults and type hints are strictly observed.

## Test Strategy

### Unit Testing Approach
- Instantiate the `CycleState` and assert that the new fields (`is_refactoring`, `current_auditor_index`, `audit_attempt_count`) initialize precisely to their defined defaults (`False`, `1`, `0`).
- Ensure type strictness (e.g., assigning a string to `current_auditor_index` fails if using Pydantic).

### Integration Testing Approach
- Validate that the existing graph (prior to Cycle 02 routing changes) does not crash or improperly merge states when these new fields are present in the payload. Mock any external API calls during these graph compilation tests.