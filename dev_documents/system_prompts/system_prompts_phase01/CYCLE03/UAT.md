# CYCLE 03 UAT: Async Dispatcher & Concurrent Execution

## Test Scenarios
- **Scenario ID 03-01:** Basic Concurrent Execution
  - Priority: Critical
  - Executing `ac-cdd run-cycle --id all --parallel` with no cycle dependencies successfully initiates and completes all cycles (e.g., 01 to 08) faster than the sequential method.
  - This verifies the primary throughput goal of the NITPICKERS upgrade.

- **Scenario ID 03-02:** DAG Scheduled Execution
  - Priority: High
  - If Cycle 02 explicitly depends on Cycle 01 being `COMPLETED`, the dispatcher must not start Cycle 02 until Cycle 01 finishes, while allowing Cycle 03 to run in parallel with Cycle 01.
  - This proves that dependency resolution correctly manages inter-cycle conflicts.

- **Scenario ID 03-03:** Rate Limit Recovery (429 Backoff)
  - Priority: Medium
  - Simulated `HTTP 429` errors from LLM APIs during parallel execution must trigger a retry mechanism without crashing the cycle task. The system should silently backoff and eventually succeed.

## Behavior Definitions
- **GIVEN** a manifest with three uncompleted cycles (01, 02, 03) and no dependencies
  **WHEN** the user runs `ac-cdd run-cycle --id all --parallel`
  **THEN** the system initiates three separate LangGraph executions concurrently, as verified by overlapping start times in logs.

- **GIVEN** a manifest where Cycle 02 depends on Cycle 01
  **WHEN** the parallel execution starts
  **THEN** Cycle 01 and Cycle 03 start immediately, and Cycle 02 is blocked until Cycle 01 reaches `COMPLETED` status.

- **GIVEN** an API client (Jules/OpenRouter) that throws a mocked `429 Too Many Requests` response
  **WHEN** a cycle task attempts to call it
  **THEN** the API client catches the exception, sleeps for a jittered duration (e.g., `random.uniform(1, 3)` seconds), and retries the call successfully.
