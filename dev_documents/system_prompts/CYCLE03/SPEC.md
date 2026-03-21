# Cycle 03: GitHub Write Operations & Jules Orchestration

## Summary
Cycle 03 is the final, highest-risk phase of the MCP transition. It involves replacing the core repository mutation mechanisms (e.g., Git branch creation, pushing commits, opening PRs) and parallel agent session orchestration with their respective MCP counterparts (`@modelcontextprotocol/server-github` for writes, and `@google/jules-mcp` for agent orchestration). This completes the removal of all custom Python API wrappers. By moving write operations to standard tools, the `master_integrator.py` node handles conflict resolution and pull request generation flawlessly. Concurrently, `global_refactor.py` leverages Jules MCP to spawn ephemeral, parallel agents without relying on legacy Python polling loops.

## System Architecture

```text
/
├── src/
│   ├── domain_models/
│   │   └── **mcp_schema.py**      (MODIFIED: Adds Jules config types)
│   ├── **mcp_client_manager.py**  (MODIFIED: Handles GitHub Write and Jules MCP connections)
│   ├── nodes/
│   │   ├── **master_integrator.py** (MODIFIED: Binds GitHub write tools)
│   │   ├── **global_refactor.py**   (MODIFIED: Binds Jules MCP tools)
│   │   └── **audit_orchestrator.py**(MODIFIED: Binds Jules MCP tools)
│   ├── templates/
│   │   ├── **MASTER_INTEGRATOR_INSTRUCTION.md** (MODIFIED: Utilizes push_commit and create_pull_request)
│   │   └── **REFACTOR_INSTRUCTION.md** (MODIFIED: Utilizes create_session and review_changes)
│   ├── services/
│   │   ├── git/                   (DELETED: Legacy custom Git tracking)
│   │   ├── git_ops.py             (DELETED: Legacy Git wrappers)
│   │   ├── integration_usecase.py (REFACTORED: Removes manual Git logic, mapped to MCP)
│   │   ├── jules/                 (DELETED: Legacy Jules API wrappers)
│   │   ├── jules_client.py        (DELETED: Legacy Jules API wrappers)
│   │   └── jules_session_state.py (REFACTORED: Relies on MCP states, removes polling)
├── tests/
│   ├── unit/
│   │   └── **test_cycle03_mechanical_gate.py** (MODIFIED: Tests mechanical gating for writes)
│   └── ac_cdd/
│       └── integration/
│           ├── **test_git_robustness.py** (MODIFIED: Relies on GitHub MCP)
│           └── **test_end_to_end_workflow.py** (MODIFIED: Tests full E2E workflow on mock repos)
```

## Design Architecture

### Pydantic Schema Design: `mcp_schema.py`
Extend `mcp_schema.py` to support Jules MCP.
- **`JulesMcpConfig`**: A validated Pydantic model enforcing that `JULES_API_KEY` is present.
- **Invariants and Constraints**:
  - `api_key` must match basic Jules token patterns.
  - `command` is set to `npx` with strict arguments `["-y", "@google/jules-mcp"]`.
- **Consumers**: `McpClientManager` consumes this configuration to instantiate the Jules connections.

### Component Design: `mcp_client_manager.py`
- Extend the manager to initialize the `@google/jules-mcp` via `get_jules_tools()`.
- Add `get_github_write_tools()` which returns `push_commit`, `create_pull_request`, `create_branch`, etc., and explicitly limits its consumption to the `master_integrator.py` node.

## Implementation Approach

1. **Schema and Config Update**:
   - Update `src/domain_models/mcp_schema.py` to add `JulesMcpConfig`.
2. **Manager Extension**:
   - Update `src/mcp_client_manager.py` to initialize `@google/jules-mcp` and expose `get_jules_tools()`. Implement `get_github_write_tools()` for authorized nodes.
3. **Agent Node Refactoring**:
   - Refactor `src/nodes/master_integrator.py` to instantiate the `McpClientManager`, call `get_github_write_tools()`, and bind them via `.bind_tools()`.
   - Refactor `src/nodes/global_refactor.py` and `src/nodes/audit_orchestrator.py` to bind Jules MCP tools (`create_session`, `review_changes`).
4. **Prompt Updates**:
   - Update the system prompts (`MASTER_INTEGRATOR_INSTRUCTION.md`, `REFACTOR_INSTRUCTION.md`) to instruct the LLMs to use the bound tools natively.
5. **Legacy Cleanup**:
   - Substantially refactor `src/services/integration_usecase.py` to remove manual git subprocess logic. Refactor `src/jules_session_state.py` to remove HTTP polling and pagination loops.
   - Delete all deprecated legacy files in `src/services/git/` and `src/services/jules/`.

## Test Strategy

### Unit Testing Approach
- **Objective**: Ensure `McpClientManager` correctly filters and binds write tools only to specific authorized nodes (Mechanical Gate). Ensure Jules tool initialization succeeds.
- **Implementation**: Update `tests/unit/test_cycle03_mechanical_gate.py`. Attempt to invoke `push_commit` from the `auditor.py` node and assert that the tool execution is firmly rejected. Validate `JulesMcpConfig`.

### Integration Testing Approach
- **Objective**: Verify full GitHub mutation logic and complex multi-agent parallel dispatching.
- **Implementation**: Update `tests/ac_cdd/integration/test_git_robustness.py` to test end-to-end conflict resolution and branching via MCP tools.
- **Tests**:
  - `test_mechanical_gate_permissions`: Ensures write tools are correctly walled off.
  - `test_mcp_jules_session_dispatch`: Asserts `global_refactor.py` uses Jules MCP to correctly dispatch parallel agents and returns diffs.
  - Execute `tests/ac_cdd/integration/test_end_to_end_workflow.py` pointing the entire system at an isolated test repository to validate the Strangler Fig migration is functionally complete.