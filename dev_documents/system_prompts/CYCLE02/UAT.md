# CYCLE02: User Acceptance Testing

## Test Scenarios

### SCENARIO-02-01: Serial Auditor Loop Progression
- **Priority**: High
- **Description**: Verify the graph correctly routes through 3 sequential auditors before refactoring.

## Behavior Definitions

```gherkin
FEATURE: Coder Graph Serial Routing

  SCENARIO: Successful traversal of serial auditors
    GIVEN the coder graph is executing
    AND the sandbox evaluation passes
    WHEN the state reaches the auditor routing
    THEN it MUST loop exactly 3 times
    AND transition to the `refactor_node` subsequently
    AND set `is_refactoring` to True
```