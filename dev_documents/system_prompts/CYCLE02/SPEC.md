# Cycle 02: Concurrent Dispatcher & Workflow Modification

## 1. Summary
Cycle 02 fundamentally transforms the execution model of the NITPICKERS architecture from a sequential process to a highly parallelised, concurrent engine. The goal is to maximize throughput (Massive Throughput) by allowing multiple development cycles to execute simultaneously, mirroring a team of engineers working concurrently on different features. This cycle entirely replaces the synchronous `for` loop in the `run-cycle` command with an asynchronous dispatcher leveraging `asyncio.gather`. Crucially, this dispatcher must maintain strict isolation between the parallel LangGraph workflows. It must also implement sophisticated network-layer resilience, specifically handling the inevitable HTTP 429 (Too Many Requests) errors that arise when blasting multiple LLM requests concurrently, using exponential backoff and jitter. Furthermore, the dispatcher will be enhanced with a basic Directed Acyclic Graph (DAG) scheduler to respect dependencies between cycles, ensuring that a cycle does not start before its prerequisite schemas or interfaces are finalized and locked.

## 2. System Architecture
The core modifications will occur within `src/ac_cdd_core/services/workflow.py` and a newly introduced `async_dispatcher.py`. The existing `WorkflowService.run_cycle` method (when invoked with `--id all`) will be refactored to utilize the `AsyncDispatcher`. The dispatcher will parse the `ProjectManifest` to determine the pending cycles and their dependencies. It will then instantiate multiple, independent `JulesClient` sessions and trigger their respective LangGraph workflows concurrently.

### File Structure Modification
```ascii
.
├── src/
│   └── ac_cdd_core/
│       ├── services/
│       │   ├── **workflow.py**
│       │   └── **async_dispatcher.py** (New)
│       ├── **state_manager.py**
│       ├── **config.py**
│       └── **jules_client.py**
```

## 3. Design Architecture
The implementation requires careful management of asynchronous state and robust error handling.

1.  **AsyncDispatcher Interface**: A new class, `AsyncDispatcher`, will be responsible for taking a list of cycle IDs, resolving their dependencies (if any are specified in the manifest), and executing them using `asyncio.gather`.
2.  **State Isolation**: We must ensure that each concurrently executing LangGraph workflow maintains its own distinct `CycleState` and `MemorySaver` instance to prevent data corruption or race conditions between parallel cycles. The `StateManager` will be updated to handle atomic writes if necessary.
3.  **Resilience Configuration**: The `config.py` module will be updated to include parameters for the exponential backoff strategy (e.g., `MAX_RETRIES=5`, `BASE_DELAY=2s`, `JITTER=True`) specifically targeting API rate limits.
4.  **Client Update**: The `JulesClient` (or the underlying LiteLLM/OpenRouter wrapper) must be wrapped or configured to automatically catch 429 HTTP errors and apply the configured backoff strategy before propagating the exception up to the graph execution loop.

## 4. Implementation Approach
The implementation focuses on safely tearing out the synchronous loop and replacing it with robust asynchronous orchestration.

1.  **Implement Resilience**: First, modify `src/ac_cdd_core/services/jules_client.py` (or the network layer) to include the retry logic for 429 errors. Use a robust library like `tenacity` or implement a custom async exponential backoff wrapper.
2.  **Create AsyncDispatcher**: Implement `src/ac_cdd_core/services/async_dispatcher.py`. This class will contain the `dispatch_all_pending(manifest)` method.
3.  **Refactor WorkflowService**: Modify `WorkflowService.run_cycle` in `src/ac_cdd_core/services/workflow.py`. When `cycle_id` is "all", it should invoke the `AsyncDispatcher` instead of iterating sequentially. Ensure that the LangGraph `CompiledStateGraph.ainvoke` method is used for true asynchronous execution.
4.  **Implement DAG Scheduler (Optional but highly recommended)**: Within the `AsyncDispatcher`, read dependencies from the `ProjectManifest`. If Cycle 02 depends on Cycle 01, use `asyncio.Event` or a task queue to hold Cycle 02 until the task representing Cycle 01 completes successfully.
5.  **State Management Safety**: Review `src/ac_cdd_core/state_manager.py` to ensure that saving the project state file (`.ac_cdd/project_state.json`) does not encounter race conditions when multiple cycles complete simultaneously. Consider using file locking or atomic rename operations.

## 5. Test Strategy
Testing concurrency is notoriously difficult; the strategy must rely on heavy mocking and controlled execution environments.

**Unit Testing Approach**: We will write unit tests for the `AsyncDispatcher` using `pytest.mark.asyncio`. We will mock the LangGraph execution (`CompiledStateGraph.ainvoke`) to simulate tasks that take varying amounts of time to complete (e.g., using `asyncio.sleep`). We will assert that the `asyncio.gather` correctly manages the futures and that the total execution time is roughly equal to the longest task, not the sum of all tasks, proving parallel execution. We will also unit test the network resilience logic by mocking the API client to explicitly return 429 errors and asserting that the backoff logic is triggered correctly without crashing the test.

**Integration Testing Approach**: We will run a mocked end-to-end multi-cycle project. We will configure the mock `JulesClient` to respond immediately. The goal is to observe the system dispatching multiple branches (`feature/cycle-01`, `feature/cycle-02`, etc.) simultaneously via the GitManager. We must assert that the final `project_state.json` accurately reflects the completion of all cycles without any state corruption or lost updates, verifying the integrity of the parallel state management.
