# CYCLE 04 UAT: E2B Sandbox Pipeline (Agentic TDD)

## Test Scenarios
- **Scenario ID 04-01:** Sandbox Red-Green-Refactor Flow (Success)
  - Priority: Critical
  - A test suite that fails (Red) followed by an implementation that passes (Green) must successfully proceed to the Auditor node. This validates the Agentic TDD constraint.

- **Scenario ID 04-02:** Sandbox Red-Green-Refactor Flow (Failure - Test Pass Too Early)
  - Priority: High
  - If a generated test passes immediately (before the feature is implemented), the pipeline must detect this and fail back to the Coder. This prevents "cheating" by generating empty tests or tests without assertions.

- **Scenario ID 04-03:** Sandbox Red-Green-Refactor Flow (Failure - Broken Implementation)
  - Priority: Critical
  - If the test fails (Red) but the subsequent implementation also fails (Red), the pipeline must loop back to the Coder with the full stack trace of the failure. It must retry until it reaches max retries or passes.

## Behavior Definitions
- **GIVEN** a newly generated feature and test in the `coder_session_node`
  **WHEN** the test is sent to the E2B Sandbox for execution and `exit_code > 0` (Red)
  **THEN** the orchestrator acknowledges the successful failing test and proceeds to request the implementation.

- **GIVEN** a feature implementation and a previously failed test
  **WHEN** the complete code is sent to E2B and executed, resulting in `exit_code == 0` (Green)
  **THEN** the orchestrator extracts the artifacts, marks the cycle as `READY_FOR_AUDIT`, and transitions to the `auditor_node`.

- **GIVEN** a feature implementation and a failing test
  **WHEN** the complete code is executed in E2B, resulting in `exit_code > 0` (Red)
  **THEN** the orchestrator sets `status = UAT_FAILED`, appends the standard error trace to the context, and routes back to the Coder with a "Fix this error" prompt.

- **GIVEN** a newly generated test in the `coder_session_node`
  **WHEN** the test is executed in E2B *before* implementation, resulting in `exit_code == 0` (Green)
  **THEN** the orchestrator immediately sets `status = UAT_FAILED` and prompts the Coder: "Test passed immediately; it must fail first to prove valid assertions."
