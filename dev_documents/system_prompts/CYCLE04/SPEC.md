# CYCLE04 Specification

## Summary
Cycle 04 orchestrates the overarching workflow that binds the discrete 5-Phase pipeline together. This cycle focuses on the CLI entry points and the primary `WorkflowService` responsible for the parallel execution of the Coder Phase (Phase 2), the sequential integration (Phase 3), and the final QA validation (Phase 4). The key implementation detail is the `run_cycle` or `run_pipeline` command, which must asynchronously dispatch the required number of `CycleState` instances, wait for their independent completion, and then funnel the aggregated results into the Integration Graph. This is the macro-level orchestration that transforms the individual graphs into a cohesive, highly parallelized development machine.

## Infrastructure & Dependencies
- **A. Project Secrets (`.env.example`):** The orchestration layer utilizes the core LLM orchestration model (e.g., Anthropic or OpenAI) for the overarching Architect Phase (Phase 1). Ensure `OPENROUTER_API_KEY` or equivalent is in `.env.example` with `# Target Project Secrets`.
- **B. System Configurations (`docker-compose.yml`):** The parallel execution of multiple Coder sessions requires sufficient resources and potentially configured concurrency limits within `docker-compose.yml`. Ensure valid YAML formatting and preserve existing environmental configurations.
- **C. Sandbox Resilience (CRITICAL TEST STRATEGY):** *All external API calls triggered by the Orchestration layer, specifically the parallel dispatching of graph executions, MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*. If tests attempt to spin up multiple live LangGraph instances hitting real APIs, the system will immediately rate-limit and fail.

## System Architecture
This cycle constructs the core orchestrator and refines the CLI access points.

**src/cli.py** (Modify)
- Refactor the `run_pipeline` or `run_cycle` commands to instantiate the `WorkflowService` and manage the execution flow.

**src/services/workflow.py** (Modify/Create)
- Implement the async execution logic for Phase 2 (building and running `_create_coder_graph` in parallel).
- Implement the sequential transition logic from Phase 2 -> Phase 3 -> Phase 4.

The architecture ensures that the execution order is strictly enforced: Phase 1 generates N specs -> Phase 2 runs N cycles concurrently until all reach END -> Phase 3 merges N results -> Phase 4 evaluates the final output.

## Design Architecture
The primary domain object here is the configuration or state management of the `WorkflowService`. It must manage an array of `CycleState` futures or tasks. The invariants require that Phase 3 cannot begin until all Phase 2 tasks yield a final, successful state. If any Phase 2 task fails unrecoverably (exceeds retry limits), the workflow must halt and report the failure. The consumers of the `WorkflowService` are the CLI entry points, while the producers are the underlying LangGraph instances. This design promotes a clear separation between the high-level orchestration logic and the granular node-level execution.

## Implementation Approach
1.  **Workflow Service Refactoring:** Within `src/services/workflow.py`, utilize `asyncio.gather` or a similar mechanism to concurrently execute multiple instances of `_create_coder_graph` corresponding to the cycles generated in Phase 1.
2.  **Phase Transition Gating:** Implement the strict gating logic: wait for all parallel Coder graphs to finish. Collect their resulting Git branches or state outputs. Pass these to the `_create_integration_graph`. Upon successful integration, pass the state to `_create_qa_graph`.
3.  **CLI Updates:** Update `src/cli.py` to correctly invoke the refactored `WorkflowService` methods. Provide clear, synchronous console output using Rich to represent the status of the parallel asynchronous tasks.
4.  **Extensive Mock Testing:** The Coder agent must mock the entire LangGraph execution within the `WorkflowService` unit tests to maintain Sandbox Resilience.

## Test Strategy

### Unit Testing Approach (Min 300 words)
The unit testing strategy for the orchestration layer demands precise control over asynchronous Python execution and comprehensive mocking. The Coder agent must generate tests using Pytest and `pytest-asyncio` to validate the `WorkflowService` in isolation. The tests must employ `pytest-mock` to intercept the actual LangGraph invocations (e.g., `graph.invoke` or `.astream`). By returning predefined, successful state dictionaries asynchronously, the unit tests can perfectly simulate the concurrent execution of multiple Phase 2 cycles without executing a single real LangGraph node. The assertions must verify that `asyncio.gather` correctly aggregates these mocked responses and that the service subsequently calls the mock Integration Graph precisely once with the correct aggregated data. Furthermore, error handling must be rigorously tested by configuring one of the mock Phase 2 tasks to raise an exception or return a failed state, asserting that the orchestrator correctly halts the pipeline and does not proceed to Phase 3. This rigorous mocking strategy strictly adheres to Sandbox Resilience, guaranteeing lightning-fast test execution.

### Integration Testing Approach (Min 300 words)
Integration testing for the Phase 4 orchestration logic must validate the overarching sequence without relying on live API keys or complex parallel network requests. The tests must construct a simplified, entirely mocked set of LangGraph instances representing Phase 2, Phase 3, and Phase 4. The integration test will invoke the CLI entry point or the `WorkflowService.run_pipeline` method directly. Crucially, adhering to the DB Rollback Rule, any persistent state modifications (such as mock CLI output logs) must utilize Pytest `tmp_path` fixtures. The test must assert that the orchestrator successfully kicks off the mock Phase 2 processes, waits for their simulated completion, initiates Phase 3, and correctly propagates the state to Phase 4. This end-to-end validation within a controlled, fully mocked environment confirms the structural integrity of the high-level orchestrator before attempting real, parallel LLM invocations.
