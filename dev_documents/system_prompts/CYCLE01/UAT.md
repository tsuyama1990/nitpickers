# CYCLE 01 Specification: Core State & Scenario Definition UAT

## Test Scenarios

### Scenario ID: 01-A (CycleState Initialization)
**Priority:** High
**Description:** The new `CycleState` fields must initialize correctly with default values, ensuring backward compatibility with existing nodes that do not require these fields.

### Scenario ID: 01-B (IntegrationState Initialization)
**Priority:** High
**Description:** The `IntegrationState` must initialize correctly and hold the correct types for its defined attributes.

## Behavior Definitions

### Scenario 01-A: Initializing CycleState
```gherkin
GIVEN a new CycleState is created
WHEN the state object is instantiated
THEN is_refactoring is False
AND current_auditor_index is 1
AND audit_attempt_count is 0
```

### Scenario 01-B: Initializing IntegrationState
```gherkin
GIVEN a new IntegrationState is created
WHEN the state object is instantiated with branches_to_merge
THEN the branches_to_merge field is a valid list of strings
AND conflict_files is empty by default
AND global_sandbox_status is unset
```