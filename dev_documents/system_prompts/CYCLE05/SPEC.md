# CYCLE 05 Specification: Workflow Orchestration (Pipeline CLI)

## Summary
CYCLE 05 is the final phase, implementing the overarching orchestration logic in `src/cli.py` and `src/services/workflow.py`. This cycle connects the previously built graphs (Coder, Integration, QA) into a seamless, automated pipeline capable of running parallel implementation cycles and sequentially integrating and testing them.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
- No new secrets. All keys used across the pipeline must be active.

### B. System Configurations (`docker-compose.yml`)
- No structural changes to `docker-compose.yml`.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
- **Mandate Mocking:** When testing the CLI `run-pipeline` command or `WorkflowService`, all sub-graph executions (`build_coder_graph().invoke`, etc.) MUST be mocked to prevent the entire system from launching during a unit test.
- Use `unittest.mock.AsyncMock` (where applicable) to simulate the successful return states of the parallel execution.

## System Architecture

```text
src/
├── **cli.py**                    # Entrypoints (`run-pipeline` modifications)
├── **services/workflow.py**      # `run_full_pipeline` orchestration logic
tests/
├── **test_workflow.py**          # Unit tests for concurrent graph execution
├── **test_cli.py**               # Unit tests for CLI entrypoints
```

## Design Architecture

### `src/services/workflow.py`
The `WorkflowService` must act as the ultimate orchestrator.

1.  **`run_full_pipeline()` (New/Refactored):**
    -   **Parallel Execution (Phase 2):** Use `asyncio.gather` (or equivalent parallel execution strategies depending on LangGraph's async support) to launch multiple instances of `_create_coder_graph` simultaneously for every defined cycle in `dev_documents/system_prompts/`.
    -   **Synchronization:** Wait for all parallel Coder cycles to reach their `END` state.
    -   **Integration Phase (Phase 3):** Once all Coder graphs complete, invoke a single instance of `_create_integration_graph` using the list of completed cycle branch names.
    -   **UAT Phase (Phase 4):** If the Integration Phase succeeds, invoke a single instance of `_create_qa_graph`.

### `src/cli.py`
The CLI must expose the orchestration logic.

1.  **`run_pipeline` Command:**
    -   Update the command to instantiate the `WorkflowService` and call `run_full_pipeline()`.
    -   Ensure proper logging to stdout to indicate the current phase (Phase 1, 2, 3, 4) to the user.

## Implementation Approach

1.  **Implement Orchestrator:**
    -   Open `src/services/workflow.py`.
    -   Implement the logic to gather all cycle IDs, spawn their respective Coder graphs in parallel, collect the results, and sequentially trigger Integration and QA.

2.  **Update CLI:**
    -   Open `src/cli.py`.
    -   Ensure `run-pipeline` correctly triggers the new workflow logic.

## Test Strategy

### Unit Testing Approach
-   **File:** `tests/test_workflow.py`
-   **Objectives:**
    -   Mock `build_coder_graph`, `build_integration_graph`, and `build_qa_graph`.
    -   Assert that `run_full_pipeline` calls the Coder graph N times (where N is the number of mocked cycles).
    -   Assert that `build_integration_graph` is called only after the Coder graphs complete.
    -   Assert that `build_qa_graph` is called only if the integration graph is successful.

### Integration Testing Approach
-   **Objectives:** Execute the CLI command in a fully mocked environment to ensure the Typer app correctly parses arguments and invokes the underlying workflow service without errors.