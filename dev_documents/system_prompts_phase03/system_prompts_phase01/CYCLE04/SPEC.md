# CYCLE 04 Specification: E2B Sandbox Pipeline (Agentic TDD)

## Summary
The goal of CYCLE 04 is to enforce the **Zero-Trust Validation** rule using the `e2b-code-interpreter`. The AI (Coder node) will no longer be trusted to simply say "my code is perfect." Instead, it must engage in a strict Agentic Test-Driven Development (TDD) loop: **Red-Green-Refactor**.
The system will synchronize the generated code and test scripts (`test_*.py`) to the E2B Sandbox, execute `pytest`, extract the physical artifacts (stdout, stderr, exit code), and feed them back to the state. If tests fail (or if they inappropriately pass in the "Red" phase), the code is immediately rejected and sent back to the Coder.

## System Architecture
This cycle involves fully implementing the `E2BExecutorService` and integrating it into the `uat_evaluate_node` (and potentially the `coder_session_node` for immediate red-green checks).

### File Structure Blueprint
```text
/
├── pyproject.toml
├── src/
│   ├── graph.py                   (Update: Add TDD validation routing)
│   ├── nodes/
│   │   └── sandbox_evaluator.py   (New: Isolated implementation for uat_evaluate_node)
│   └── services/
│       ├── uat_usecase.py         (Update: Use E2BExecutorService)
│       └── e2b_executor.py        (New: Manages sandbox synchronization and execution)
└── tests/
    └── unit/
        ├── test_e2b_executor.py   (New)
        └── test_uat_usecase.py    (Update)
```
**Modifications:**
- **`src/services/e2b_executor.py`**: A new service using the E2B SDK to run isolated `bash` commands (e.g., `uv run pytest tests/` or similar). It maps the results to `E2BExecutionResult`.
- **`src/nodes/sandbox_evaluator.py`**: The `uat_evaluate_node` is relocated here. It pushes code to E2B, runs the UAT scripts generated in `UAT.md`, and evaluates success based purely on the `exit_code`.

## Design Architecture
### Pydantic Models & Extensibility
1. **`E2BExecutorService` Interface:**
   - Methods: `async push_files(local_path, remote_path)`, `async run_tests(command: str) -> E2BExecutionResult`, `async cleanup()`.
   - It requires the `E2B_API_KEY` from the environment.
2. **Red-Green-Refactor Flow:**
   - The Coder must generate a failing test *first*. The pipeline sends it to E2B. If it exits with `0` (Green), it means the test is improperly written (e.g., no assertions). The pipeline fails back to the Coder stating: "Test passed immediately; it must fail first."
   - The Coder then implements the logic and sends the code again. If it exits with `> 0` (Red), the pipeline fails back with the `stderr` logs attached. "Tests failed. Fix the following traceback: [...]"

### Isolation Constraints
E2B Sandboxes are ephemeral. The `E2BExecutorService` must spin up a container, sync the current feature branch's `src` and `tests` directories, install dependencies (e.g., via `uv sync`), and run the test suite. All side-effects remain inside E2B. The exit code is the sole determinant of success.

## Implementation Approach
1. **E2B Service Wrapper:** In `src/services/e2b_executor.py`, use `e2b_code_interpreter.Sandbox` to implement the required interface.
2. **TDD Validation Node:** In `src/graph_nodes.py`, the `uat_evaluate_node` (and potentially a new `tdd_evaluate_node` directly after `coder_session_node` before `auditor_node`) will:
   - Instantiate `E2BExecutorService`.
   - Sync files.
   - Run `pytest -v --tb=short`.
   - Store `E2BExecutionResult` into `CycleState.sandbox_artifacts`.
   - Return `FlowStatus.UAT_FAILED` or `FlowStatus.READY_FOR_AUDIT` (if green).
3. **Traceback Feedback:** If `UAT_FAILED`, the node concatenates the raw `stdout` and `stderr` and injects it into a strict prompt: "Execution failed. Fix this: [logs]" and routes back to `coder_session`.

## Test Strategy
### Unit Testing Approach
- Develop `test_e2b_executor.py`. Mock the `e2b_code_interpreter.Sandbox` API responses to simulate `exit_code=0` (success) and `exit_code=1` (failure). Assert that `E2BExecutionResult` captures the mocked `stdout` and `stderr`.
- Develop `test_uat_usecase.py`. Mock the `E2BExecutorService` returning failures, and verify that the UseCase correctly maps the failure to `FlowStatus.UAT_FAILED` and populates the `CycleState.error` field.

### Integration Testing Approach
- Without a real E2B key during standard CI, test the routing logic by forcefully injecting an `E2BExecutionResult` with `exit_code=1` into the state and validating that the LangGraph transition goes from `uat_evaluate` $\rightarrow$ `coder_session` (simulating the Red-Green-Refactor loop).
- Ensure the injected `error` string properly escapes the raw stack trace text before sending it to Jules.
