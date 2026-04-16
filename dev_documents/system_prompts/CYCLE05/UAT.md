# CYCLE05: User Acceptance Testing

## Test Scenarios

### SCENARIO-05-01: Full 5-Phase Pipeline Orchestration
- **Priority**: Critical
- **Description**: Verify the CLI correctly orchestrates parallel coding followed by sequential integration and QA.

## Behavior Definitions

```gherkin
FEATURE: Master Pipeline Orchestration

  SCENARIO: Parallel to Sequential Transition
    GIVEN a requirement parsed into 3 distinct cycles
    WHEN the user executes the full pipeline command
    THEN the system MUST launch 3 Coder graphs concurrently
    AND the Integration graph MUST NOT start until all 3 Coder graphs complete
    AND the QA graph MUST ONLY execute if Integration succeeds
```