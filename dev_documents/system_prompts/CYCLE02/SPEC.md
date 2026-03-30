# CYCLE 02 Specification: Routers and Node logic

## Summary
The primary goal of CYCLE 02 is to implement the new routing logic in `src/nodes/routers.py` (`route_sandbox_evaluate`, `route_auditor`, `route_final_critic`) and refactor `_create_coder_graph` in `src/graph.py` to establish the serial auditor loop and the refactoring bypass.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
- No new external APIs or secret dependencies are introduced in this cycle.

### B. System Configurations (`docker-compose.yml`)
- No structural changes to `docker-compose.yml` are required for core state modifications.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
- Any unit tests verifying node and router behavior must mock `E2B_API_KEY`, `JULES_API_KEY`, `OPENROUTER_API_KEY`. The Sandbox will not possess real API keys during automated model validations.
- Mocking: `unittest.mock` must be used for testing the router's behavior without executing actual agent nodes.

## System Architecture

```text
src/
├── **nodes/routers.py**         # New conditional edge routing logic
├── **graph.py**                 # Refactored `_create_coder_graph` for the Coder phase
tests/
├── **test_routers.py**          # Unit tests for the routers
├── **test_graph.py**            # Unit tests for the graph routing loops
```

## Design Architecture

### `src/nodes/routers.py`
The Routers define pure functional logic to direct the flow of the LangGraph state based on `CycleState`.

1.  **`route_sandbox_evaluate(state: CycleState) -> str`**:
    -   **Logic:**
        -   If `state.sandbox_status` == "failed", return "failed".
        -   If success AND `state.is_refactoring` == True, return "final_critic".
        -   Otherwise, return "auditor".

2.  **`route_auditor(state: CycleState) -> str` (New)**:
    -   **Logic:**
        -   If current review is "Reject", increment `audit_attempt_count`. If `audit_attempt_count` > max_attempts (e.g., 2), route back with a final warning or break loop. Otherwise, return "reject" (back to coder).
        -   If "Approve", increment `current_auditor_index`.
        -   If `current_auditor_index` > 3, return "pass_all" (move to refactoring).
        -   Otherwise, return "next_auditor".

3.  **`route_final_critic(state: CycleState) -> str` (New)**:
    -   **Logic:** Self-evaluation. If NG, return "reject" (back to coder). If OK, return "approve" (END).

### `src/graph.py` (`_create_coder_graph`)
The core routing diagram from `ALL_SPEC.md` must be exactly reproduced. Existing `committee_manager` and `uat_evaluate` logic must be removed. `self_critic` must be placed right after the coder but before the sandbox on the first run. The graph structure must reflect the `route_sandbox_evaluate`, `route_auditor`, and `route_final_critic` edges.

## Implementation Approach

1.  **Routers Implementation:**
    -   Open `src/nodes/routers.py`.
    -   Create or update the functions (`route_sandbox_evaluate`, `route_auditor`, `route_final_critic`) with strict typing matching `CycleState`.

2.  **Graph Restructuring:**
    -   Open `src/graph.py` and modify `_create_coder_graph`.
    -   Add nodes: `coder_session`, `self_critic`, `sandbox_evaluate`, `auditor_node`, `refactor_node`, `final_critic_node`.
    -   Define the edges according to the `ALL_SPEC.md` specification. Remove obsolete nodes from this specific graph.

3.  **Node Modifications (Minor):**
    -   Ensure `refactor_node` successfully sets `state["is_refactoring"] = True`.

## Test Strategy

### Unit Testing Approach
-   **File:** `tests/test_routers.py`
-   **Objectives:** Verify every possible state permutation in `route_sandbox_evaluate` (e.g., failed, passed + refactoring, passed + not refactoring) to ensure correct string returns.
-   **Objectives:** Test `route_auditor` for rejection counting, approval incrementing, and the `pass_all` threshold.

### Integration Testing Approach
-   **File:** `tests/test_graph.py`
-   **Objectives:** Create a mock graph traversal that sets pre-determined states (using a Checkpointer or explicit state injection) to ensure the Coder graph traverses the full path: Coder -> Sandbox -> Auditor (loop 3 times) -> Refactor -> Sandbox -> Final Critic -> END.