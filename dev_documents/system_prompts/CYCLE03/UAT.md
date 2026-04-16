# CYCLE03: User Acceptance Testing

## Test Scenarios

### SCENARIO-03-01: 3-Way Diff Prompt Generation
- **Priority**: High
- **Description**: Verify the Conflict Manager correctly extracts and formats the 3 states of a conflicted file.

## Behavior Definitions

```gherkin
FEATURE: 3-Way Diff Conflict Resolution

  SCENARIO: Formatting the conflict prompt
    GIVEN a Git repository with a conflicted file
    WHEN the system calls `build_conflict_package`
    THEN the output MUST contain the "### Base" section
    AND the output MUST contain the "### Branch A" section
    AND the output MUST contain the "### Branch B" section
    AND standard inline Git conflict markers (<<<<<<<) SHOULD NOT be strictly relied upon for the prompt context
```