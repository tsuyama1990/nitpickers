# CYCLE 07 UAT: Stateful Master Integrator Session

## Test Scenarios
- **Scenario ID 07-01:** Successful Stateful Conflict Resolution
  - Priority: Critical
  - When the integration branch contains multiple conflicted files, a single, stateful Master Integrator session is created. It successfully resolves all files sequentially without losing context or hallucinating markers.

- **Scenario ID 07-02:** Conflict Marker Retry Loop
  - Priority: High
  - If the Master Integrator returns a "resolved" file that still contains standard Git conflict markers (e.g., `<<<<<<<`), the system must immediately reject it and prompt the same session to fix it.
  - This prevents bad merges from proceeding to the next file or the final commit.

- **Scenario ID 07-03:** Maximum Conflict Retries Exceeded
  - Priority: Medium
  - If the Master Integrator fails to produce a clean file after the maximum number of retries (e.g., 3), the system must halt the integration process, leave the branch in the conflict state, and notify the user for manual intervention.

## Behavior Definitions
- **GIVEN** a `ConflictRegistry` with 2 conflicted files (`fileA.py`, `fileB.py`)
  **WHEN** the integration phase begins
  **THEN** a new Jules session is created (`IntegrationState.jules_session_id`) and `fileA.py` is sent for resolution.
  **AND** upon successful clean resolution, `fileB.py` is sent to the *same* session via a follow-up message.

- **GIVEN** a Master Integrator session resolving `fileA.py`
  **WHEN** the returned code still contains the string `<<<<<<< HEAD`
  **THEN** `validate_resolution` returns `False`. The system appends an error message ("Conflict markers remain!") to the prompt history and resends it to the active session.

- **GIVEN** a Master Integrator session resolving `fileA.py` that fails validation 3 consecutive times
  **WHEN** the loop reaches the maximum retry limit
  **THEN** the system logs a critical failure, aborts the current automated integration step, and exits cleanly, leaving `fileA.py` unresolved for manual review.