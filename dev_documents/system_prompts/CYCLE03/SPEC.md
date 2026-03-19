# CYCLE03 SPECIFICATION

## Summary
This cycle implements Phase 1: The Inner Loop (Structural Integrity & TDD). We will introduce Backend Verification and Gatekeeping as a mechanical blockade. The orchestration layer must be updated to enforce strict type checking (`uv run mypy .`) and linting (`uv run ruff check .`) dynamically. If any non-zero exit code is detected, it will automatically block PR creation and kick the stderr trace back to Jules's active session. This structural integrity phase acts as the first line of defense in the zero-trust validation model, preventing obviously broken code from consuming expensive multi-modal outer loop resources. It firmly places the responsibility of syntax, style, and type correctness on the Stateful Worker before any behavioral verification occurs. The core implementation revolves around extending the existing `ProcessRunner` and modifying the LangGraph routing nodes to consume its execution outputs deterministically.

## System Architecture
The architecture introduces synchronous blocking operations via the `ProcessRunner` (located in `src/process_runner.py`). The `ProcessRunner` acts as the execution interface for all shell commands, capturing both standard output (`stdout`) and standard error (`stderr`). The orchestration nodes (specifically `src/nodes/coder.py` or equivalent test evaluator nodes within the LangGraph workflow) will consume the `ProcessRunner`'s output to make deterministic routing decisions.

If `mypy` or `ruff` yields a non-zero exit code, the state manager captures the `uat_exit_code` and the accompanying error log. The LangGraph conditional edges must be updated to evaluate this state: instead of advancing to the PR creation node, the graph routes the execution flow back to the `coder` node. This enforcing logic represents the structural backbone of zero-trust execution. The architecture dictates that the `ProcessRunner` must securely execute shell commands without vulnerability to command injection, utilizing `shlex.quote()` where appropriate, and executing asynchronously via `asyncio.create_subprocess_exec` to avoid blocking the main event loop during long-running static analysis.

```text
/
├── src/
│   ├── **process_runner.py**
│   ├── nodes/
│   │   ├── **coder.py**
│   │   └── **routers.py**
│   └── services/
│       └── **workflow.py**
```

## Design Architecture
The design utilizes the `ProcessRunner` interface. The implementation requires extending `ProcessRunner` methods to strictly parse and return the combined output of linting and type-checking commands as a structured data object.

The domain models established in CYCLE01 (e.g., `UATResult`) will be utilized to serialize the output logs to ensure determinism within the LangGraph state.
Key constraints:
1.  **Security**: The `ProcessRunner` must strictly sanitize inputs.
2.  **Concurrency**: It must execute asynchronously via `asyncio.create_subprocess_exec` to prevent event loop blocking.
3.  **State Management**: The node executing these checks (`coder.py` or a dedicated `structural_check.py` node) must correctly mutate the `uat_exit_code` and `stderr` fields of the global state dictionary before passing the vector back to the router.
4.  **Routing logic**: The conditional logic in `routers.py` must explicitly check `state.get('uat_exit_code', 0) != 0` to decide whether to route back to the worker or advance.

## Implementation Approach
The implementation requires modifying `src/process_runner.py` to ensure it captures comprehensive test logs correctly.

**Step 1:** Extend `ProcessRunner` in `src/process_runner.py` with a method like `async def run_structural_checks(self, directory: str) -> UATResult:`. This method will sequence `uv run ruff check .` and `uv run mypy .`.

**Step 2:** Ensure it correctly awaits `create_subprocess_exec` and reads the output streams without deadlocking. Capture the exit code. If `ruff` fails, immediately return the result; otherwise, run `mypy`.

**Step 3:** We will integrate this execution step within the workflow nodes (`src/nodes/coder.py` or a dedicated node). Call `await runner.run_structural_checks()`.

**Step 4:** Update the state dictionary with the result (`uat_exit_code` and `stderr`).

**Step 5:** Modify the LangGraph router (`src/nodes/routers.py` or `src/graph.py`) to systematically evaluate the `uat_exit_code`. If the exit code is not zero, the LangGraph router directs the flow back to the Stateful Worker. This step mechanically prohibits advancing if structural integrity is compromised.

## Test Strategy

### Unit Testing Approach
The unit testing approach will thoroughly test the `ProcessRunner` logic using `unittest.mock.patch` on `asyncio.create_subprocess_exec`. We will verify that simulated non-zero exit codes correctly bubble up as parsed error messages in the `UATResult` object. We must write tests simulating a successful `ruff` run followed by a failing `mypy` run, ensuring the sequential execution halts correctly and captures the specific error stream. We will also test the `shlex` sanitization to ensure directory paths are properly quoted.

### Integration Testing Approach
The integration testing approach will execute the node transition logic within a mock LangGraph context. We will simulate a state where the structural check node returns a non-zero exit code due to a `ruff` failure. We will verify that the router correctly evaluates the state dictionary and directs the workflow back to the coding node, absolutely preventing transition to the PR creation node. This satisfies the mechanical blockade requirement. We will run a parallel test simulating a clean run (exit code 0) and verify the workflow routes forward successfully.
