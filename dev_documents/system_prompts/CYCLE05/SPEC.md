# CYCLE 05: CLI & Workflow Orchestration

## Summary
The purpose of Cycle 05 is to finalize the global orchestration logic that binds the 5-Phase Architecture together. The `WorkflowService.run_full_pipeline` method will be updated to orchestrate Phase 1 through Phase 4 sequentially and concurrently.

This cycle defines the logic for triggering the parallel execution of the `coder_graph` (Phase 2), waiting for their collective completion, triggering the single `integration_graph` (Phase 3), and finally invoking the independent `qa_graph` (Phase 4).

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
*Target Project Secrets:* No new external APIs are introduced. Existing keys (JULES_API_KEY, E2B_API_KEY, OPENROUTER_API_KEY) are sufficient.

### B. System Configurations (`docker-compose.yml`)
*Non-confidential configurations:* Ensure the Sidecar path variables are maintained.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
*Mandate Mocking:* You MUST explicitly instruct the Coder that *all external API calls relying on the newly defined secrets in `.env.example` MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*.
The workflow orchestration relies heavily on asynchronous event loops (`asyncio.gather`). Unit tests for this class MUST heavily utilize `AsyncMock` to simulate graph execution and strictly verify the order of calls to `builder.build_coder_graph().ainvoke()`, `builder.build_integration_graph().ainvoke()`, and `builder.build_qa_graph().ainvoke()`.

## System Architecture

The following file structure must be implemented or modified to support global workflow orchestration:

```text
src/
├── **cli.py**                  # Adjust the run_cycle / run_pipeline commands.
└── services/
    └── **workflow.py**           # Update `run_full_pipeline` logic.
```

## Design Architecture

This cycle focuses on robustly coordinating the entire pipeline's state and execution flow.

1.  **`src/services/workflow.py` (`run_full_pipeline`)**:
    *   **Domain Concept**: Master orchestrator connecting all 5 phases dynamically.
    *   **Constraints**:
        *   Retrieve the planned cycles from the active `CycleManifest` generated in Phase 1.
        *   Execute Phase 2: Launch `_run_single_cycle` for all planned cycles using `asyncio.gather` (or the existing `AsyncDispatcher.run_with_semaphore`) to run the Coder Graphs in parallel. Wait for *all* tasks to finish.
        *   If Phase 2 completely succeeds, execute Phase 3: Instantiate an `IntegrationState` and invoke `integration_graph.ainvoke()`.
        *   If Phase 3 completely succeeds, execute Phase 4: Instantiate a global `CycleState` and invoke `qa_graph.ainvoke()`.
        *   If any phase fails or raises an unhandled exception, the process MUST halt and exit immediately (e.g., `sys.exit(1)`) preventing corrupted sequential data from passing forward.
    *   **Consumers**: `run-pipeline` CLI command.

2.  **`src/cli.py` (`app` Typer instance)**:
    *   **Domain Concept**: Exposes the system via command-line interface.
    *   **Constraints**: Ensure the `run-pipeline` (or equivalent master command) is documented clearly and directly maps to `WorkflowService.run_full_pipeline`. Ensure `run-cycle` remains for individual Phase 2 debugging.

## Implementation Approach

1.  **Update `WorkflowService`**: Open `src/services/workflow.py`. Locate the `run_full_pipeline` method.
    *   Refactor the `asyncio.gather` logic for Phase 2. Ensure exceptions are caught (`return_exceptions=True`) and evaluated. If any task returns an exception, log the failure and `sys.exit(1)`.
    *   Instantiate `IntegrationState` with the `manifest.feature_branch`. Execute `integration_graph.ainvoke(...)`. If `conflict_status == "failed"`, `sys.exit(1)`.
    *   Instantiate `CycleState` with `cycle_id="99"`, `current_phase=WorkPhase.QA`, `status=FlowStatus.START`. Execute `qa_graph.ainvoke(...)`. If `status == "failed"`, `sys.exit(1)`.
2.  **Update `cli.py`**: Open `src/cli.py`. Ensure the typper command for running the full pipeline natively invokes this newly robust `run_full_pipeline` function and handles top-level generic exceptions gracefully.

## Test Strategy

All tests must be executed without real LLM API calls, strictly using local, mocked dependencies.

**Unit Testing Approach (Min 300 words):**
We must test the execution order inside `WorkflowService.run_full_pipeline`. Create tests in `tests/unit/services/test_workflow.py`.
*   **Test Synchronous Order Enforcement**: Using `pytest.MonkeyPatch` and `AsyncMock`, mock the graph building and invocation methods on `GraphBuilder`.
    *   Mock `build_coder_graph().ainvoke()` to instantly return a successful state for two concurrent cycles.
    *   Mock `build_integration_graph().ainvoke()` to instantly return a successful `IntegrationState`.
    *   Mock `build_qa_graph().ainvoke()` to instantly return a successful final `CycleState`.
    *   Execute `run_full_pipeline`.
    *   Assert that the invocation order was strictly enforced: `coder_graph` instances called simultaneously -> wait -> `integration_graph` called -> wait -> `qa_graph` called.
*   **Test Early Termination on Phase Failure**: Repeat the previous test but mock `build_coder_graph().ainvoke()` to raise an exception or return an error state. Assert that `SystemExit` is raised and that `build_integration_graph` and `build_qa_graph` are *never* called.

**Integration Testing Approach (Min 300 words):**
We must test the `run-pipeline` CLI command End-to-End. Create tests in `tests/live/test_e2e_cli.py` (or a dedicated integration equivalent).
*   **Test E2E CLI Run via Subprocess**: Do NOT use `typer.testing.CliRunner`. Use Python's `subprocess.run` to execute the system `nitpick run-pipeline` command within a generated temporary project directory containing a dummy `ALL_SPEC.md` and mock `.env`.
*   Verify the process initializes the environment, generates manifest structures, correctly triggers the parallel mock LLM processes (as seen in simulated standard output logs), integrates them smoothly via the mock Git manager, and passes the dummy QA graph. The process must exit with code `0`. Use `# noqa: S603` for Ruff compliance.