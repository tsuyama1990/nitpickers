# CYCLE 04: Phase 4 UAT & QA Graph Adaptation

## Summary
The goal of Cycle 04 is to solidify Phase 4: the UAT & QA Graph. In the legacy architecture, UAT was tightly coupled to individual coding cycles. In the new 5-Phase Architecture, End-to-End User Acceptance Testing (e.g., Playwright scripts running against the integrated system) must be decoupled and executed *only* after Phase 3 (Integration) has successfully completed.

This cycle refactors the `uat_usecase.py` and the `_create_qa_graph` to operate independently, ensuring they trigger based on the global state of the project session rather than a specific cycle implementation.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
*Target Project Secrets:* No new external APIs are introduced. Existing keys (OPENROUTER_API_KEY for multimodal vision analysis) are strictly required for the `qa_auditor`.

### B. System Configurations (`docker-compose.yml`)
*Non-confidential configurations:* Ensure the Sidecar path variables are maintained.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
*Mandate Mocking:* You MUST explicitly instruct the Coder that *all external API calls relying on the newly defined secrets in `.env.example` MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*.
The `uat_evaluate_node` will likely execute external test frameworks like Playwright. During unit/integration testing, these node executions MUST be mocked to instantly return successful or failed traces without spinning up real browser instances.

## System Architecture

The following file structure must be implemented or modified to support Phase 4 UAT & QA decoupling:

```text
src/
├── **graph.py**                  # Adjust _create_qa_graph initialization.
└── services/
    └── **uat_usecase.py**        # Decouple from Phase 2 triggers.
```

## Design Architecture

This cycle focuses on ensuring the QA graph is fully independent.

1.  **`src/services/uat_usecase.py`**:
    *   **Domain Concept**: Manages the execution of E2E tests and analysis of their outputs.
    *   **Constraints**:
        *   Remove any legacy triggers that invoked UAT directly from the Phase 2 Coder graph.
        *   Must be initialized with a global `CycleState` representing the entire project session (e.g., `cycle_id="qa"`).
    *   **Consumers**: `WorkflowService.run_full_pipeline` (in Phase 4).

2.  **`src/graph.py` (`_create_qa_graph`)**:
    *   **Domain Concept**: Orchestrates the execution nodes for final system validation.
    *   **Constraints**:
        *   Ensure START -> `uat_evaluate`.
        *   Conditionally route from `uat_evaluate`: if `status == FAILED`, route to `qa_auditor`. Otherwise, route to `ux_auditor` or END.
        *   Ensure `qa_auditor` -> `qa_session` -> `qa_regression_sandbox_node` -> conditionally back to `qa_session` (if failed) or `uat_evaluate` (if passed).

## Implementation Approach

1.  **Decouple `uat_usecase`**: Open `src/services/uat_usecase.py`. Remove any tight coupling that expects a specific Coder `CycleState` containing individual file changes. The UAT evaluation should assume the code is already present on the active branch (integrated).
2.  **Verify `_create_qa_graph`**: Open `src/graph.py`. Locate the `_create_qa_graph` method.
    *   Initialize a `StateGraph(CycleState)`.
    *   Ensure nodes are registered: `qa_session`, `qa_auditor`, `qa_regression_sandbox_node`, `uat_evaluate`, `ux_auditor`.
    *   Ensure the conditional routing logic exactly matches the architectural requirements listed above.

## Test Strategy

All tests must be executed without real LLM API calls, strictly using local, mocked dependencies.

**Unit Testing Approach (Min 300 words):**
We must test the modified `uat_usecase.py` to ensure it initializes and executes correctly given a standalone state. Create tests in `tests/unit/services/test_uat_usecase.py`.
*   **Test Standalone Initialization**: Instantiate `UatUsecase` with a dummy `CycleState(cycle_id="qa-session")`. Mock its internal execution methods. Assert that it runs without requiring inherited attributes from a previous Phase 2 cycle.

**Integration Testing Approach (Min 300 words):**
We must test the `_create_qa_graph` flow using deterministic mocks. Create tests in `tests/integration/test_qa_graph.py`.
*   **Test Clean UAT Path**: Mock `uat_evaluate_node` to succeed instantly (returning a `UatAnalysis` indicating success). Execute the graph. Verify the execution trace hits `uat_evaluate`, routes to `ux_auditor`, and terminates at `END`.
*   **Test QA Remediation Loop**: Mock `uat_evaluate_node` to return a "failed" status initially, and "passed" on the second invocation. Mock `qa_auditor_node`, `qa_session_node`, and `qa_regression_sandbox_node` to simulate successful analysis, code fixing, and basic unit test passing respectively. Execute the graph. Verify the trace loops: `uat_evaluate` -> `qa_auditor` -> `qa_session` -> `qa_regression_sandbox_node` -> `uat_evaluate` -> `ux_auditor` -> `END`. Use an `AsyncMock` for node execution to prevent coroutine warnings.