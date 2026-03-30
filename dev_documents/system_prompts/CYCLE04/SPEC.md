# CYCLE 04 Specification: UAT Decoupling & QA Graph

## Summary
CYCLE 04 focuses on completely separating User Acceptance Testing (UAT) from the individual feature cycles (Phase 2). UAT will now execute exclusively as Phase 4 (QA Graph) on the unified codebase after Phase 3 (Integration) completes successfully.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
- Uses `OPENROUTER_API_KEY` for Vision LLM diagnostics and `JULES_API_KEY` for QA Session fixes.

### B. System Configurations (`docker-compose.yml`)
- Playwright system dependencies (already present in the current implementation) are required for taking UI screenshots during UAT evaluation.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
- Unit tests involving `uat_usecase.py` and QA graph nodes MUST heavily mock Playwright execution, file-system writing of screenshots, and external Vision LLM calls. Tests must not actually launch browsers unless designated as live integration tests with isolated environments.

## System Architecture

```text
src/
├── **services/uat_usecase.py**   # Redesigned to operate solely as a post-integration evaluation
├── **graph.py**                  # _create_qa_graph implementation
tests/
├── **test_uat_usecase.py**       # Unit tests for independent UAT execution
```

## Design Architecture

### `src/services/uat_usecase.py`
The `UatUsecase` must be refactored to consume the unified project state rather than a specific cycle's state.

1.  **State Decoupling:**
    -   Previously, UAT was tightly coupled to `CycleState` and executed per feature. Now, it must read from a more generic state (or the final unified workspace) to execute the predefined `USER_TEST_SCENARIO.md` scripts (e.g., Marimo notebooks or standard Playwright tests).
    -   It acts as the primary validation gate, producing artifacts (screenshots, logs) if failures occur.

### `src/graph.py` (`_create_qa_graph`)
A dedicated LangGraph for Phase 4.

1.  **Nodes:**
    -   `uat_evaluate_node`: Executes E2E tests across the integrated project.
    -   `qa_auditor_node`: An OpenRouter-based Vision LLM that analyzes screenshots/logs from failed tests to produce a diagnosis and fix plan.
    -   `qa_session_node`: A Jules-based agent that implements the fix plan.
2.  **Edges:**
    -   `START` -> `uat_evaluate_node`
    -   `uat_evaluate_node` -> Conditional -> "pass" (`END`), "fail" (`qa_auditor_node`)
    -   `qa_auditor_node` -> `qa_session_node`
    -   `qa_session_node` -> `uat_evaluate_node` (Retry evaluation)

## Implementation Approach

1.  **Refactor `UatUsecase`:**
    -   Open `src/services/uat_usecase.py`.
    -   Ensure its execution logic no longer relies on variables specific to an individual coding cycle. It should simply execute the tests in the global workspace.

2.  **Implement `_create_qa_graph`:**
    -   Open `src/graph.py`.
    -   Ensure `_create_qa_graph` matches the routing logic specified in the ALL_SPEC.md. (Current implementation might already be close, verify and adjust edges).

3.  **Update Routing Logic:**
    -   In `src/nodes/routers.py`, verify or create the conditional logic used by `uat_evaluate_node`.

## Test Strategy

### Unit Testing Approach
-   **File:** `tests/test_uat_usecase.py`
-   **Objectives:**
    -   Verify that executing the UAT use case without a specific cycle ID still successfully runs tests in the global workspace (mocked).
    -   Verify that artifacts (screenshots) are correctly packaged into the state for the `qa_auditor_node` when tests fail.

### Integration Testing Approach
-   **Objectives:** Mock a failed Playwright run, ensure the QA Auditor receives the mock screenshot, generates a mock plan, passes it to the QA Session, and successfully retries.