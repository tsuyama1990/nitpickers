# CYCLE 03 Specification: Async Dispatcher & Concurrent Execution

## Summary
The core of NITPICKERS throughput relies on executing development cycles simultaneously. CYCLE 03 focuses on refactoring the sequential `run-cycle` logic in `workflow.py` into an `asyncio`-driven, concurrent execution pipeline. Instead of iterating through cycles one-by-one, the system will kick off multiple `CycleState` instances as parallel LangGraph tasks. To ensure stability, an API rate-limit handler (jittered backoff) and a basic DAG scheduler (to respect cycle dependencies, e.g., Cycle 02 cannot start until Cycle 01 is merged) will be introduced.

## System Architecture
This cycle involves modifying `src/workflow.py` to enable concurrency and `src/services/` to handle async dispatching.

### File Structure Blueprint
```text
/
├── pyproject.toml
├── src/
│   ├── workflow.py              (Update: Replace synchronous for-loops with async execution)
│   ├── cli.py                   (Update: Add --parallel flag to run-cycle)
│   └── services/
│       └── async_dispatcher.py  (New: Manages concurrent tasks, rate limits, and scheduling)
└── tests/
    └── unit/
        ├── test_workflow.py     (Update)
        └── test_dispatcher.py   (New)
```
**Modifications:**
- **`src/workflow.py`**: Rewrite `_run_all_cycles` to use `async_dispatcher.py`.
- **`src/services/async_dispatcher.py`**: A new service wrapping `asyncio.gather` with semaphores and HTTP 429 backoff logic.
- **`src/cli.py`**: Allow a user to trigger parallel runs, e.g., `ac-cdd run-cycle --id all --parallel`.

## Design Architecture
### Pydantic Models & Extensibility
1. **`DispatcherConfig`:**
   - Properties: `max_concurrent_tasks` (int), `retry_backoff_factor` (float), `max_retries` (int).
   - This defines the global rules for API interactions during parallel operations.
2. **DAG Scheduling Logic:**
   - Extend `CycleManifest` (in `state_manager.py`) to optionally list `depends_on: list[str]`.
   - The Dispatcher only yields a cycle for execution if its dependencies' statuses are `COMPLETED`.

### Network Robustness
Since running multiple cycles concurrently increases the risk of `HTTP 429 Too Many Requests` from LLM APIs (OpenRouter, Jules), the `async_dispatcher` must intercept these errors globally and apply an exponential backoff with jitter (e.g., `asyncio.sleep(random.uniform(1, 3))`) before retrying the exact API call.

## Implementation Approach
1. **Dispatcher Service:** Create `AsyncDispatcher` class in `src/services/async_dispatcher.py`. Use an `asyncio.Semaphore(max_concurrent_tasks)` to limit simultaneous LangGraph invocations (default 6).
2. **Workflow Update:** In `src/workflow.py`, refactor `_run_all_cycles`. Instead of `await graph.ainvoke()` in a simple loop, map all uncompleted cycles to tasks:
   ```python
   async def dispatch_cycles():
       tasks = [dispatcher.run(cycle_id) for cycle_id in planned_cycles]
       await asyncio.gather(*tasks)
   ```
3. **DAG Resolution:** Before `asyncio.gather`, resolve a topological sort of the cycles based on `depends_on` from the manifest. Execute batches of independent cycles sequentially (e.g., [Cycle01] $\rightarrow$ [Cycle02, Cycle03] $\rightarrow$ [Cycle04]).
4. **API Retry Decorator:** Implement a generic `@retry_on_429` decorator or modify the `jules_client.py` and `llm_reviewer.py` to catch `HTTPStatusError` (429) and implement jittered sleep.
5. **CLI Integration:** Add the `--parallel` flag in Typer (`cli.py`).

## Test Strategy
### Unit Testing Approach
- Develop `test_dispatcher.py` to assert that the `AsyncDispatcher` correctly batches dependent and independent cycles based on a mock manifest. For example, if A depends on nothing, and B and C depend on A, it should execute A alone, then B and C concurrently.
- Test the retry decorator by mocking an API call that throws a `429` exception twice and succeeds on the third try. Verify that it backs off exponentially and does not fail the execution.

### Integration Testing Approach
- In `test_workflow.py`, mock the LangGraph execution to complete immediately and assert that all cycles are executed concurrently (e.g., by checking execution timestamps or mocking the graph invocation to track parallel calls).
- Verify that standard logging handles parallel outputs gracefully without severe interleaving corruption (e.g., utilizing `rich` progress bars effectively for multiple concurrent tasks).