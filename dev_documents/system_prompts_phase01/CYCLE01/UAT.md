# CYCLE 01 UAT: Domain Models & State Management Extension

## Test Scenarios
- **Scenario ID 01-01:** Backward Compatible State Initialization
  - Priority: High
  - The system must be able to initialize `CycleState` without the new concurrent fields, relying on their default values.
  - This guarantees that resuming an older session before the upgrade will not cause runtime errors.

- **Scenario ID 01-02:** Conflict & Sandbox State Assignment
  - Priority: High
  - The new models `ConflictRegistryItem` and `E2BExecutionResult` must accept inputs correctly and reject invalid types according to Pydantic definitions.
  - This prevents bad data from failing the LangGraph pipeline down the line.

- **Scenario ID 01-03:** Source Path Verification
  - Priority: Critical
  - Verify that the CLI executes successfully after migrating from `dev_src/ac_cdd_core` to `src/`. No `ModuleNotFoundError` should occur.

## Behavior Definitions
- **GIVEN** a new session is initialized
  **WHEN** a `CycleState` is created without specifying `conflict_status` or `sandbox_artifacts`
  **THEN** the system must assign their default values (e.g., `None` and an empty `dict`) and allow the program to run.

- **GIVEN** an active E2B testing step
  **WHEN** `E2BExecutionResult` is populated with `exit_code="0"` (string)
  **THEN** Pydantic must coerce it to an integer or throw a validation error, but an integer `0` must be stored.

- **GIVEN** an active conflict resolution step
  **WHEN** a `ConflictRegistryItem` is populated with a `file_path` and `conflict_markers` list
  **THEN** the object must properly serialize to a dictionary for saving into the LangGraph state JSON.

- **GIVEN** a command line input `ac-cdd init`
  **WHEN** executed by the user
  **THEN** the CLI app must load from `src/cli.py` and output the initialization message successfully.
