# CYCLE 01 Specification: Domain Models & State Management Extension

## Summary
The goal of CYCLE 01 is to establish the fundamental domain models, state management structures, and enums required for the concurrent and robust execution of the NITPICKERS framework. By modifying the existing state management, we provide a foundation that enables future cycles to implement parallel execution, track conflicts, and store dynamic execution artifacts from sandbox UATs. In addition to expanding the Pydantic models, this cycle includes safely moving the source code directory from `dev_src/ac_cdd_core` to `src/` to align with the final target structure, maintaining backward compatibility where necessary. This ensures the rest of the architecture has a strong, type-safe blueprint.

## System Architecture
This cycle involves the refactoring of existing modules to include new states, enums, and properties that support concurrent logic.

### File Structure Blueprint
```text
/
├── pyproject.toml
├── src/
│   ├── __init__.py
│   ├── state.py                (Update: Extend CycleState with new properties)
│   ├── domain_models.py        (Update: Add ConflictRegistryItem, E2BExecutionResult)
│   ├── enums.py                (Update: Add new states for conflict and sandbox)
│   └── ...
└── tests/
    └── unit/
        ├── test_state.py       (Create/Update)
        └── test_domain_models.py (Create/Update)
```
**Modifications:**
- Move `dev_src/ac_cdd_core` to `src/` directly.
- **`src/state.py`**: Extend `CycleState`.
- **`src/domain_models.py`**: Add new schema components.
- **`src/enums.py`**: Define `FlowStatus` and `SessionStatus` additions.

## Design Architecture
### Pydantic Models & Extensibility
1. **`CycleState` Extension:**
   - Add a `sandbox_artifacts: dict[str, Any]` field to temporarily hold output from E2B tests.
   - Add a `conflict_status: FlowStatus | None` to indicate if the cycle is currently blocked by merge conflicts.
   - Add a `concurrent_dependencies: list[str]` to allow DAG scheduling to verify dependencies.
2. **`ConflictRegistryItem`:**
   - Properties: `file_path` (str), `conflict_markers` (list of markers detected), `resolution_attempts` (int), `resolved` (bool).
   - Expected Producers: GitManager parsing.
   - Expected Consumers: Master Integrator Jules Session.
3. **`E2BExecutionResult`:**
   - Properties: `stdout` (str), `stderr` (str), `exit_code` (int), `coverage_report` (str | None).
   - Invariants: `exit_code` strictly determines test pass/fail.

### Backward Compatibility
Since we are migrating `ac_cdd_core` to `src/`, all existing relative imports within `src/` must remain valid. Any external CLI references in `pyproject.toml` pointing to `ac_cdd_core` must be updated appropriately. This step does not change the core LangGraph logic but merely enriches the state.

## Implementation Approach
1. **Source Migration:** Move `dev_src/ac_cdd_core` to `src/`. Update `pyproject.toml` to reflect the new paths. Replace any explicit paths referencing `dev_src` in tests or configuration files.
2. **Enum Additions:** In `src/enums.py`, update `FlowStatus` to include constants like `UAT_FAILED`, `CONFLICT_DETECTED`, and `CONFLICT_RESOLVED`. Update `SessionStatus` if needed.
3. **Domain Model Additions:** In `src/domain_models.py`, implement `ConflictRegistryItem` and `E2BExecutionResult` adhering to strict Pydantic definitions (using `BaseModel`, `Field` for descriptions).
4. **State Extension:** In `src/state.py`, modify `CycleState` to include `sandbox_artifacts` and `conflict_status`. Ensure default values are provided so legacy state processing does not fail.
5. **Code Review & Linting:** Run `ruff` and `mypy --strict` to ensure the new models are strictly typed and have maximum McCabe complexity under 10.

## Test Strategy
### Unit Testing Approach
- Develop `test_state.py` to ensure `CycleState` can be instantiated without breaking old initialization patterns (backward compatibility). Verify that the new fields, like `sandbox_artifacts` and `conflict_status`, can be correctly accessed and modified.
- Create `test_domain_models.py` to test the instantiation of `ConflictRegistryItem` and `E2BExecutionResult`. Ensure that Pydantic's inherent type checking raises `ValidationError` for malformed inputs (e.g., passing a string to `exit_code`).

### Integration Testing Approach
- Simulate state serialization/deserialization to ensure that `StateManager` successfully saves and loads the new fields.
- Assert that imports from `src/` function correctly within the CLI context, proving the migration from `dev_src/ac_cdd_core` was successfully resolved. Mock any dependencies on the LangGraph execution to isolate the state verification.