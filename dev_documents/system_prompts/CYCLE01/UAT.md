# CYCLE 01: State Management UAT

## Test Scenarios

### Scenario ID: UAT-01-01 (Priority: High)
**Description:** Verify that `CycleState` accurately initializes and correctly maps properties to its sub-state `CommitteeState`.
**Setup:** A simple Python script within a Marimo notebook to instantiate the state model without external dependencies.
**Execution (Mock Mode):**
*   Instantiate `CycleState` with a dummy `cycle_id`.
*   Assert `is_refactoring` is `False`.
*   Assert `current_auditor_index` is `1`.
*   Assert `audit_attempt_count` is `0`.
*   Mutate the properties directly on `CycleState`.
*   Assert the changes correctly propagate to the `committee` property.
**Verification:** All assertions must pass silently. If a property is missing or mismatched, the assertion will fail.

### Scenario ID: UAT-01-02 (Priority: Medium)
**Description:** Verify that `CommitteeState` validation logic rejects invalid configuration values (e.g., negative attempt counts).
**Setup:** A Marimo notebook block executing a try-except validation check.
**Execution (Mock Mode):**
*   Attempt to instantiate `CommitteeState(current_auditor_index=0)`.
*   Catch `ValidationError`.
*   Attempt to instantiate `CommitteeState(audit_attempt_count=-1)`.
*   Catch `ValidationError`.
**Verification:** The validation errors must be raised specifically matching the constraints defined in `src/state_validators.py`.

## Behavior Definitions

**Feature:** State Management for 5-Phase Architecture
**As a** system orchestrator,
**I want** to track the current serial auditor, audit attempt count, and refactoring status,
**So that** I can accurately route execution flows during the coding phase without relying on implicit variables.

**Scenario:** Initialize the CycleState with default values
**GIVEN** the orchestrator requests a new `CycleState` object
**WHEN** the object is instantiated with only a `cycle_id`
**THEN** the `is_refactoring` flag should be `False`
**AND** the `current_auditor_index` should be `1`
**AND** the `audit_attempt_count` should be `0`

**Scenario:** Map properties seamlessly to CommitteeState
**GIVEN** an active `CycleState` object
**WHEN** the orchestrator updates `state.is_refactoring = True`
**THEN** the internal `state.committee.is_refactoring` property must also evaluate to `True`
**AND** setting `state.current_auditor_index = 2` must reflect in `state.committee.current_auditor_index`

**Scenario:** Prevent invalid state transitions through validation
**GIVEN** an active `CycleState` object
**WHEN** an invalid transition attempts to set `state.current_auditor_index = 0`
**THEN** a `ValidationError` should be immediately raised, blocking the transition.