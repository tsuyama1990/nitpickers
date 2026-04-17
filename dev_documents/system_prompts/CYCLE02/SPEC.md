# CYCLE02: Phase 2 Coder Graph Refactoring

## Summary
CYCLE02 involves redefining the LangGraph structure for the Coder Phase (`_create_coder_graph`). We will replace the existing parallel committee logic with a deterministic, serial audit loop utilizing the state flags introduced in CYCLE01.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
- Target Project Secrets:
  - `OPENROUTER_API_KEY`: Required for the serial `auditor_node`.

### B. System Configurations (`docker-compose.yml`)
- No new environment variables needed for Docker compose in this cycle.

### C. Sandbox Resilience
- **Mandate Mocking**: All OpenRouter API calls from the `auditor_node` MUST be mocked using `pytest-mock` to prevent infinite retry loops in CI environments that lack real API keys.

## System Architecture

Modifications target the graph compilation and routing logic.

```text
nitpickers/
└── src/
    ├── **graph.py**
    └── nodes/
        └── **routers.py**
```

## Design Architecture

- **`src/graph.py` (`_create_coder_graph`)**:
  - Drops existing `committee_manager` and `uat_evaluate` logic.
  - Wires the new serial pipeline: `START -> coder_session -> self_critic (1st pass only) -> sandbox_evaluate`.
  - Wires conditional edges from `sandbox_evaluate` to either `auditor_node` or `final_critic_node`.
- **`src/nodes/routers.py`**:
  - `route_sandbox_evaluate`: Routes to `coder_session` if "failed", to `final_critic` if `is_refactoring == True`, else to `auditor`.
  - `route_auditor`: Manages `audit_attempt_count` increments on "reject". Advances `current_auditor_index` on "approve". Returns "pass_all" if `current_auditor_index > 3`.
  - `route_final_critic`: Routes to `coder_session` on reject, or `END` on approve.

## Implementation Approach

1.  Open `src/nodes/routers.py`. Implement `route_sandbox_evaluate`, `route_auditor`, and `route_final_critic` per the design constraints.
2.  Open `src/graph.py`. Locate `_create_coder_graph`.
3.  Remove legacy parallel node setups.
4.  Register nodes: `coder_session`, `self_critic`, `sandbox_evaluate`, `auditor_node`, `refactor_node`, `final_critic_node`.
5.  Establish standard edges and conditional edges utilizing the functions from `routers.py`.
6.  Ensure `refactor_node` implicitly sets `state["is_refactoring"] = True` before transitioning to `sandbox_evaluate`.

## Test Strategy

### Unit Testing Approach
- Test `route_auditor` independently. Mock states with various `audit_attempt_count` and `current_auditor_index` values. Assert it correctly returns "reject", "next_auditor", or "pass_all".

### Integration Testing Approach
- Compile `_create_coder_graph` in a test environment.
- Mock all node executables to return deterministic responses (e.g., mock the Sandbox to always pass).
- Trace the execution path to ensure a full pass navigates: Coder -> Self Critic -> Sandbox -> Auditor(1,2,3) -> Refactor -> Sandbox -> Final Critic -> END.