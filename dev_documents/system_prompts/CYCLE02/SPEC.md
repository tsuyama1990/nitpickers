# CYCLE 02: Phase 2 Coder Graph (Serial Auditing)

## Summary
The goal of Cycle 02 is to restructure the `_create_coder_graph` to enforce the serial auditing loop defined in the 5-Phase Architecture. This involves rewiring the LangGraph nodes to progress sequentially: Coder -> Sandbox -> Auditor -> Refactor -> Final Critic, rather than relying on a loosely coupled "committee_manager".

Specifically, we will implement conditional routers (`route_sandbox_evaluate`, `route_auditor`, `route_final_critic`) that intelligently utilize the new state variables (`is_refactoring`, `current_auditor_index`, `audit_attempt_count`) established in Cycle 01.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
*Target Project Secrets:* No new external APIs are introduced. Existing keys (JULES_API_KEY, E2B_API_KEY, OPENROUTER_API_KEY) are sufficient.

### B. System Configurations (`docker-compose.yml`)
*Non-confidential configurations:* Ensure the Sidecar path variables are maintained.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
*Mandate Mocking:* You MUST explicitly instruct the Coder that *all external API calls relying on the newly defined secrets in `.env.example` MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*.
The sandbox will not possess real API keys during autonomous evaluation. All LangGraph edge routing logic MUST be testable via deterministic state injections, avoiding real API calls. If `route_auditor` attempts a real network request during a test, the pipeline will fail.

## System Architecture

The following file structure must be implemented or modified to support Phase 2 serial auditing:

```text
src/
├── **graph.py**                  # Re-wire _create_coder_graph for serial execution.
└── nodes/
    └── **routers.py**            # Implement new conditional routing logic.
```

## Design Architecture

This cycle focuses on the logical transitions between LangGraph nodes based on state evaluation.

1.  **`src/nodes/routers.py` (`route_sandbox_evaluate`, `route_auditor`, `route_final_critic`)**:
    *   **Domain Concept**: Defines conditional edge logic for the `Coder Graph`.
    *   **Invariants**:
        *   `route_sandbox_evaluate`: If `state.status == FAILED`, route to "failed". If `is_refactoring == True`, route to "final_critic". Otherwise, route to "auditor".
        *   `route_auditor`: If `audit_result` is `Reject`, increment `audit_attempt_count` and return "reject" (or handle max retries). If `Approve`, increment `current_auditor_index`. If `current_auditor_index > 3`, return "pass_all". Otherwise, return "next_auditor".
        *   `route_final_critic`: If self-evaluation passes, return "approve". If it fails, return "reject".
    *   **Consumers**: `_create_coder_graph` in `src/graph.py`.

2.  **`src/graph.py` (`_create_coder_graph`)**:
    *   **Domain Concept**: Orchestrates the execution nodes for a single development cycle.
    *   **Constraints**: Must execute sequentially. `self_critic` -> `sandbox` -> `route_sandbox_evaluate` -> `auditor` -> `route_auditor` -> `refactor` -> `sandbox` -> `route_sandbox_evaluate` -> `final_critic` -> `route_final_critic`.

## Implementation Approach

1.  **Update Routers**: Open `src/nodes/routers.py`. Implement or refactor `route_sandbox_evaluate`, `route_auditor`, and `route_final_critic` according to the invariants defined above. Ensure they accept `CycleState` and return appropriate string identifiers.
2.  **Update `_create_coder_graph`**: Open `src/graph.py`. Locate the `_create_coder_graph` method.
    *   Add nodes: `coder_session`, `self_critic`, `sandbox_evaluate`, `auditor_node`, `refactor_node`, `final_critic_node`. (Reuse existing if available, mock if necessary for initial wiring).
    *   Add unconditional edges: START -> `coder_session` -> `self_critic` -> `sandbox_evaluate`.
    *   Add conditional edge from `sandbox_evaluate` using `route_sandbox_evaluate`. Route to `coder_session` (if failed), `auditor_node`, or `final_critic_node`.
    *   Add conditional edge from `auditor_node` using `route_auditor`. Route to `coder_session` (reject), `auditor_node` (next), or `refactor_node` (pass_all).
    *   Add unconditional edge from `refactor_node` -> `sandbox_evaluate`. (Ensure `refactor_node` sets `state.is_refactoring = True`).
    *   Add conditional edge from `final_critic_node` using `route_final_critic`. Route to `coder_session` (reject) or END (approve).

## Test Strategy

All tests must be executed without real LLM API calls, strictly using local, mocked dependencies.

**Unit Testing Approach (Min 300 words):**
We must test the individual routing functions in isolation. Create tests in `tests/unit/nodes/test_routers.py`.
*   **Test `route_sandbox_evaluate`**: Instantiate `CycleState` with `status="failed"`. Assert the function returns `"failed"`. Instantiate with `status="passed"` and `is_refactoring=True`. Assert the function returns `"final_critic"`. Instantiate with `status="passed"` and `is_refactoring=False`. Assert the function returns `"auditor"`.
*   **Test `route_auditor`**: Instantiate `CycleState` with an `audit_result` indicating rejection. Assert the function returns `"reject"` and that `audit_attempt_count` increments. Instantiate with `audit_result` indicating approval and `current_auditor_index=1`. Assert the function returns `"next_auditor"` and `current_auditor_index` increments to 2. Instantiate with `audit_result` indicating approval and `current_auditor_index=3`. Assert the function returns `"pass_all"`.

**Integration Testing Approach (Min 300 words):**
We must test the complete `_create_coder_graph` flow using deterministic mocks. Create tests in `tests/integration/test_coder_graph.py`.
*   **Test Happy Path**: Mock all nodes (`coder_session`, `sandbox_evaluate`, `auditor_node`, `refactor_node`, `final_critic_node`) to return successfully. Execute the graph. Verify the execution trace hits each node sequentially and terminates at `END`. Ensure `is_refactoring` toggles correctly and `current_auditor_index` increments up to 3 before reaching the refactor node.
*   **Test Auditor Rejection Loop**: Mock the `auditor_node` to reject on the first attempt, then approve. Execute the graph. Verify the trace loops back to `coder_session` (or the equivalent retry node) once, then proceeds to `refactor_node`. Ensure `audit_attempt_count` increments correctly. Use an `AsyncMock` for node execution to prevent coroutine warnings.