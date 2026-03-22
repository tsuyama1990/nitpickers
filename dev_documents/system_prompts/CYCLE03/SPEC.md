# CYCLE03 Specification: Orchestration & UAT Phase Isolation

## Summary
CYCLE03 is the final technical cycle of the refactoring process. It focuses on the high-level orchestration of the entire 5-Phase pipeline and the strict isolation of Phase 4 (UAT & QA Graph). Previously, UAT evaluation might have been prematurely triggered or tightly coupled with the Coder Phase. This cycle ensures that UATs (e.g., Playwright E2E tests) are *only* executed after all parallel Coder cycles have completed and successfully integrated via Phase 3. It involves significant updates to the `WorkflowService` and CLI to manage parallel asynchronous execution of the Coder Graphs and sequential execution of the Integration and UAT graphs.

## System Architecture
This cycle touches the highest-level orchestrators of the system, ensuring the workflow transitions logically from one phase to the next.

### File Structure Modifications
The following files will be modified:

```text
src/
├── **cli.py** (Updating run_cycle / full-pipeline commands)
└── services/
    ├── **workflow.py** (Implementing the async orchestrator)
    └── **uat_usecase.py** (Isolating the UAT logic)
```

### Components and Interactions
1.  **Workflow Orchestrator (`src/services/workflow.py`)**: The `WorkflowService` must be upgraded from a linear sequence to a parallel-aware orchestrator.
    -   It must spawn multiple `_create_coder_graph` executions asynchronously (using `asyncio.gather` or similar) for each defined cycle in the manifest.
    -   It must `await` the successful completion (reaching the `END` state) of all parallel Coder Phase graphs.
    -   Once all Coder Phases complete, it must sequentially invoke the Phase 3 `_create_integration_graph`.
    -   Only upon successful integration, it must invoke Phase 4 `_create_qa_graph` via the `uat_usecase.py`.
2.  **UAT UseCase (`src/services/uat_usecase.py`)**: This service currently might be invoked from within the Coder Phase. It must be cleanly extracted and modified to accept the final integrated state as its input. It is the sole entry point for Phase 4.
3.  **CLI (`src/cli.py`)**: The CLI commands must be updated to reflect this new orchestration model, allowing users to run a single cycle (`run-cycle --id 01`) or the entire orchestrated pipeline (`run-pipeline`).

## Design Architecture
The design philosophy here is strict sequential dependency at the macro level (Phase 1 $\rightarrow$ Phase 2 $\rightarrow$ Phase 3 $\rightarrow$ Phase 4), while allowing parallelism at the micro level (Cycle 01 || Cycle 02 inside Phase 2).

### Domain Concepts
-   **Workflow Manifest**: A list of cycles (e.g., `["01", "02"]`) that need to be executed.
-   **Phase Barrier**: A synchronization point where the orchestrator blocks until all tasks in the current phase are complete before proceeding. The barrier between Phase 2 and Phase 3 is critical.
-   **UAT Execution State**: The state model managed by `uat_usecase.py`. It must be initialized with the state of the *integrated* repository, not just a single feature branch.

### Invariants and Constraints
-   Phase 3 *must never* begin if any Phase 2 cycle fails or is still running.
-   Phase 4 (UAT) *must never* run against a non-integrated feature branch during the automated pipeline execution. It is designed to test the emergent behavior of all features combined.
-   The orchestrator must gracefully handle failures in any phase, bubbling the error up to the CLI and halting execution immediately to prevent cascaded failures.

### Extensibility and Backward Compatibility
The CLI will retain commands like `run-cycle --id 01` for backward compatibility and manual debugging of specific features. However, a new or updated `run-pipeline` (or equivalent) command will become the primary execution path for the fully automated system. The `uat_usecase.py` will maintain its internal logic for executing Playwright and analyzing failure artifacts via OpenRouter, but its entry constraints are tightened.

## Implementation Approach
The implementation focuses on asynchronous programming and structural refactoring.

1.  **Isolate UAT (`src/services/uat_usecase.py`)**:
    -   Review `uat_usecase.py` and ensure it no longer contains logic coupling it to the `coder_session` or Phase 2 `CycleState` variables directly.
    -   Ensure it can be instantiated and executed purely based on the current state of the global integration branch.

2.  **Implement Orchestrator (`src/services/workflow.py`)**:
    -   Locate or create the primary workflow execution method (e.g., `run_full_pipeline(cycles: list[str])`).
    -   **Phase 2 (Parallel)**: Create a list of asyncio tasks, one for each cycle ID, invoking `build_coder_graph` and running it to completion. Use `asyncio.gather(*tasks, return_exceptions=True)` to execute them concurrently.
    -   Inspect the results. If any task returned an exception or failed state, halt the entire workflow and report the error.
    -   **Phase 3 (Sequential)**: If all Coder graphs succeed, invoke `build_integration_graph`. Await its completion. Check for failure and halt if necessary.
    -   **Phase 4 (Sequential)**: If integration succeeds, invoke `build_qa_graph` (or call `uat_usecase.py` directly if it manages its own graph). Await completion.

3.  **Update CLI (`src/cli.py`)**:
    -   Modify the Typer commands to expose the new `run_full_pipeline` logic.
    -   Ensure the console output (e.g., using `rich`) clearly indicates which phase the system is currently executing and the status of parallel tasks.

## Test Strategy

### Unit Testing Approach (Min 300 words)
The unit testing for CYCLE03 will focus on the state transitions and exception handling within the asynchronous orchestrator in `tests/services/test_workflow.py`.

We will use `unittest.mock.AsyncMock` to simulate the execution of the LangGraph phases without actually invoking them. We will create a test suite that covers various execution paths. For example, a "Phase 2 Failure" test will mock `asyncio.gather` to return one success and one exception (simulating a failed Coder cycle). We will assert that the `run_full_pipeline` method catches this exception, correctly identifies the failing cycle, halts execution immediately, and crucially, does *not* invoke the subsequent Phase 3 integration method.

Another unit test will simulate a "Phase 3 Failure". We will mock all Phase 2 tasks to succeed, but mock the `build_integration_graph` execution to return a failed state. We will assert that the orchestrator correctly halts and does *not* proceed to Phase 4 (UAT). These unit tests ensure that the foundational control flow and barrier logic of the 5-Phase pipeline are sound, preventing the system from proceeding in an invalid state.

### Integration Testing Approach (Min 300 words)
Integration testing for CYCLE03 will verify the end-to-end execution of the CLI and the `WorkflowService` using mocked graphs but a real event loop. This will be implemented in `tests/test_pipeline_orchestration.py`.

We will use the Typer testing framework `CliRunner` to invoke the pipeline command. We will provide a dummy manifest specifying two cycles (`CYCLE01`, `CYCLE02`). We will heavily mock the internal graph factories (`_create_coder_graph`, `_create_integration_graph`, `_create_qa_graph`) to simply return successful `END` states almost immediately, avoiding any LLM calls or sandbox execution.

The test will verify that when `CliRunner.invoke(app, ["run-pipeline"])` is called, the console output indicates the start of Phase 2, the parallel execution of the two cycles, the transition to Phase 3, and finally the transition to Phase 4. We will assert that the CLI command exits with a zero exit code (`exit_code == 0`). We will also write an integration test where one of the mocked Coder graphs intentionally raises an exception, verifying that the CLI catches it, outputs an appropriate error message using `rich`, and exits with a non-zero exit code (`exit_code != 0`), confirming the pipeline's fail-fast mechanism works correctly in a fully integrated environment.