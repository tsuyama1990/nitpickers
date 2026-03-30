# CYCLE05 UAT Plan

## Test Scenarios

### Scenario 1: Marimo Tutorial "Mock Mode" Execution (Priority: Critical)
This scenario ensures that the comprehensive interactive notebook `tutorials/nitpickers_5_phase_architecture.py` executes successfully in CI environments without any required API keys, perfectly demonstrating the routing logic of all 5 Phases.

### Scenario 2: Global Orchestrator Graceful Failure Handling (Priority: High)
This scenario validates that unexpected, unhandled exceptions occurring deep within a graph execution are correctly caught by the Orchestrator, logged for diagnostics, and gracefully terminate the process with a non-zero exit code.

### Behavior Definitions

**Scenario 1: Marimo Tutorial "Mock Mode" Execution**

GIVEN a continuous integration environment lacking `OPENROUTER_API_KEY`, `E2B_API_KEY`, and `JULES_API_KEY`
WHEN the command `uv run marimo test tutorials/nitpickers_5_phase_architecture.py` is executed
THEN the tutorial script must completely bypass all external LLM and sandbox invocations via `pytest.MonkeyPatch` context or environment overrides
AND the script must successfully execute from start to finish
AND exit with a zero status code

**Scenario 2: Global Orchestrator Graceful Failure Handling**

GIVEN the `WorkflowService` orchestrating the 5-Phase pipeline
AND a critical system exception (e.g., `MemoryError` or `ValueError`) is intentionally injected into a lower-level node
WHEN the Orchestrator attempts to process the resulting state
THEN the system should catch the unhandled exception
AND write a detailed post-mortem diagnostic log to `dev_documents/`
AND the execution must terminate cleanly with a non-zero exit code, avoiding a raw Python traceback crash
