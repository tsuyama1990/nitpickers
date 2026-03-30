# CYCLE 05 Specification: Workflow Orchestration (Pipeline CLI) UAT

## Test Scenarios

### Scenario ID: 05-A (Full Pipeline Orchestration)
**Priority:** High
**Description:** The CLI must successfully orchestrate the entire 5-Phase pipeline, from parallel Coder cycles to sequential Integration and QA.

### Scenario ID: 05-B (Pipeline Failure Handling)
**Priority:** High
**Description:** The pipeline must correctly halt or handle failures in any of the sub-phases (e.g., if a Coder cycle fails, the Integration phase should not commence).

## Behavior Definitions

### Scenario 05-A: Successful Pipeline Run
```gherkin
GIVEN a project with 3 defined cycles
WHEN the nitpick run-pipeline command is executed
THEN 3 Coder graphs execute in parallel
AND when all 3 Coder graphs complete successfully
THEN 1 Integration graph executes
AND when the Integration graph completes successfully
THEN 1 QA graph executes
AND the pipeline finishes successfully
```

### Scenario 05-B: Handling Coder Failure
```gherkin
GIVEN a project with 3 defined cycles
WHEN one of the Coder graphs fails to complete
THEN the pipeline halts
AND the Integration graph is not executed
AND an error message is displayed
```