# Cycle 03: GitHub Write Operations & Jules Orchestration

## Summary
Cycle 03 is the final, highest-risk phase of the MCP transition. It involves replacing the core repository mutation mechanisms (e.g., Git branch creation, pushing commits, opening PRs) and parallel agent session orchestration with their respective MCP counterparts (`@modelcontextprotocol/server-github` for writes, and `@google/jules-mcp` for agent orchestration). This completes the removal of all custom Python API wrappers. By moving write operations to standard tools natively injected into the node scopes via Dependency Injection, the `master_integrator.py` node handles conflict resolution and pull request generation flawlessly. Concurrently, `global_refactor.py` leverages Jules MCP to spawn ephemeral, parallel agents without relying on legacy Python polling loops.

## System Architecture

```text
/
├── src/
│   ├── cli.py                 (MODIFIED: Injects GitHub Write & Jules tools into graph)
│   ├── mcp_router/
│   │   ├── **schemas.py**     (MODIFIED: Adds JulesMcpConfig via BaseSettings)
│   │   ├── **manager.py**     (MODIFIED: Handles Jules MCP subprocess context)
│   │   └── **tools.py**       (MODIFIED: Exposes get_github_write_tools and get_jules_tools)
│   ├── nodes/
│   │   ├── **master_integrator.py** (MODIFIED: Receives GitHub write tools)
│   │   ├── **global_refactor.py**   (MODIFIED: Receives Jules MCP tools)
│   │   └── **audit_orchestrator.py**(MODIFIED: Receives Jules MCP tools)
│   ├── templates/
│   │   ├── **MASTER_INTEGRATOR_INSTRUCTION.md** (MODIFIED: Utilizes push_commit)
│   │   └── **REFACTOR_INSTRUCTION.md** (MODIFIED: Utilizes create_session)
│   ├── services/
│   │   ├── git/                   (DELETED: Legacy custom Git tracking)
│   │   ├── git_ops.py             (DELETED: Legacy Git wrappers)
│   │   ├── integration_usecase.py (REFACTORED: Removes manual Git logic, maps to MCP)
│   │   ├── jules/                 (DELETED: Legacy Jules API wrappers)
│   │   ├── jules_client.py        (DELETED: Legacy Jules API wrappers)
│   │   └── jules_session_state.py (REFACTORED: Relies on MCP states, removes polling)
├── tests/
│   ├── unit/
│   │   └── **test_cycle03_mechanical_gate.py** (MODIFIED: Validates DI injection barriers)
│   └── ac_cdd/
│       └── integration/
│           ├── **test_git_robustness.py** (MODIFIED: Relies on GitHub MCP)
│           └── **test_end_to_end_workflow.py** (MODIFIED: Tests E2E on mock repos)
```

## Design Architecture

### Pydantic Settings Design: `schemas.py`
Extend `schemas.py` to support the Jules fleet manager securely.
- **`JulesMcpConfig`**: A validated subclass of `BaseSettings` enforcing `JULES_API_KEY`.
- **Invariants and Constraints**:
  - `JULES_API_KEY` must match valid string patterns and fail fast on initialization.
  - Generates the rigid `StdioServerParameters` with `command="npx"` and `args=["-y", "@google/jules-mcp"]`.

### Component Design: `manager.py` & `tools.py`
- Extend the manager context to concurrently instantiate all three servers (`e2b`, `github`, `jules`) and tear them down simultaneously on exit.
- `tools.py` introduces `get_github_write_tools()` which filters the GitHub toolset strictly for mutating tools (`push_commit`, `create_pull_request`, `create_branch`). This explicit method allows `src/cli.py` to target only the `master_integrator.py` node for injection.

## Implementation Approach

1. **Schema and Config Update**:
   - Update `src/mcp_router/schemas.py` to add `JulesMcpConfig`.
2. **Manager Extension**:
   - Update `src/mcp_router/manager.py` to initialize `@google/jules-mcp` inside the async context.
   - Update `src/mcp_router/tools.py` to expose `get_jules_tools()` and `get_github_write_tools()`.
3. **App Initialization & Injection**:
   - Update `src/cli.py` to fetch `github_write_tools` and inject them exclusively into `master_integrator.py`. Fetch `jules_tools` and inject them into `global_refactor.py` and `audit_orchestrator.py`.
4. **Agent Node Refactoring**:
   - Refactor `master_integrator.py` to accept and bind `github_write_tools`.
   - Refactor `global_refactor.py` and `audit_orchestrator.py` to accept and bind `jules_tools` (`create_session`, `review_changes`).
5. **Prompt Updates**:
   - Update `MASTER_INTEGRATOR_INSTRUCTION.md` and `REFACTOR_INSTRUCTION.md` instructing LLMs to use bound tools natively.
6. **Legacy Cleanup**:
   - Refactor `integration_usecase.py` removing `subprocess` `git` calls. Refactor `jules_session_state.py` removing legacy HTTP polling and pagination loops.
   - Delete all deprecated legacy files in `src/services/git/` and `src/services/jules/`.

## Test Strategy

### Unit Testing Approach
- **Objective**: Ensure the `mcp_router` initializes the Jules connection securely and DI accurately walls off write capabilities.
- **Implementation**: Update `tests/unit/test_cycle03_mechanical_gate.py`. Assert that `push_commit` is structurally absent from the read-only node configurations. Validate `JulesMcpConfig`. Assert `manager.py` tears down 3 separate stdio clients correctly.

### Integration Testing Approach
- **Objective**: Verify full GitHub mutation logic via MCP tools and complex multi-agent dispatching via Jules MCP.
- **Implementation**: Update `tests/ac_cdd/integration/test_git_robustness.py` asserting end-to-end conflict resolution utilizing native ToolCalls.
- **Tests**:
  - `test_mechanical_gate_permissions`: Ensures DI injection maps the correct tools.
  - `test_mcp_jules_session_dispatch`: Asserts `global_refactor.py` utilizes Jules MCP correctly to spawn parallel agent sessions and parse standard ToolMessage outputs.
  - Execute `tests/ac_cdd/integration/test_end_to_end_workflow.py` pointing the entire system at an isolated test repository validating full functional parity.