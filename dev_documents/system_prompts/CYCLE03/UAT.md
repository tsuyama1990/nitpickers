# CYCLE03 UAT

## Test Scenarios

### Scenario ID: SCENARIO-03-1
**Priority**: High
This scenario tests the mechanical blockade against linting failures. The user will trigger the agent workflow with intentionally bad Python code that violates `ruff` rules (e.g., unused imports, line length violations). They must observe that the `ProcessRunner` successfully executes `ruff`, captures the non-zero exit code and standard error trace, and mechanically halts PR creation by routing the workflow back to the inner loop worker for correction.

### Scenario ID: SCENARIO-03-2
**Priority**: High
This scenario tests the mechanical blockade against typing failures. The user will trigger the workflow with code that passes linting but contains intentional `mypy` type errors (e.g., returning an `int` from a function annotated to return `str`). They will verify that the `ProcessRunner` correctly sequences the execution, captures the `mypy` failure, and routes the typed error trace back to the Stateful Worker.

### Scenario ID: SCENARIO-03-3
**Priority**: Medium
This scenario verifies that structurally sound code bypasses the Phase 1 Inner Loop gatekeeper. The user will execute the workflow with perfect, compliant Python code. They will observe the `ProcessRunner` returning an exit code of 0 for both linting and typing, allowing the LangGraph router to advance the state to the subsequent execution phases smoothly.

## Behavior Definitions

GIVEN the generated code contains a syntax error or a `ruff` linting violation
WHEN the structural verification node (`ProcessRunner`) runs
THEN it captures a non-zero exit code from `uv run ruff check .`
AND it populates the state dictionary with the error trace
AND the workflow router immediately directs the flow back to the coder node, bypassing subsequent nodes.

GIVEN the generated code is structurally sound but contains a type annotation error
WHEN the structural verification node runs
THEN it successfully passes the `ruff` check but captures a non-zero exit code from `uv run mypy .`
AND the workflow router directs the flow back to the coder node with the precise `mypy` error trace.

GIVEN the generated code is entirely free of structural and typing defects
WHEN the structural verification node runs
THEN the `ProcessRunner` records a successful exit code (0)
AND the workflow router correctly evaluates the state to advance to the dynamic UAT testing phase or PR creation phase.
