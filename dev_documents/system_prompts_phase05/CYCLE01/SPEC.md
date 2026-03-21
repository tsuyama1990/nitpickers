# Cycle 01: E2B Sandbox Isolation

## Summary
Cycle 01 is the foundational phase for transitioning the Nitpickers application from a rigid API Wrapper architecture to a modern MCP Router paradigm. The primary focus of this cycle is to introduce the necessary Node.js infrastructure and the modular `src/mcp_router/` Python package. All E2B Cloud Sandboxing interactions will be migrated to the `@e2b/mcp-server`. This migration targets the `sandbox_evaluator` and `qa` nodes, transitioning them to natively use function calling to execute code. By delegating all bash environment interactions and evaluations to the MCP server, we eliminate custom Python wrappers and manual error parsing, resulting in a robust, deterministic execution environment injected directly into the nodes.

## System Architecture

In this cycle, we introduce the modular `mcp_router` package, relying on `pydantic-settings` to securely configure the E2B server over `stdio` via an asynchronous context manager.

```text
/
├── Dockerfile                 (MODIFIED: Adds Node.js & @e2b/mcp-server)
├── pyproject.toml             (MODIFIED: Adds mcp, langchain-mcp-adapters, pydantic-settings)
├── src/
│   ├── cli.py                 (MODIFIED: Wraps the workflow in the MCP context manager)
│   ├── mcp_router/            (NEW MODULE: Replaces legacy sandbox executors)
│   │   ├── __init__.py
│   │   ├── schemas.py         (NEW: BaseSettings for E2B configuration)
│   │   ├── manager.py         (NEW: Async Context Manager handling npx subprocess lifecycle)
│   │   └── tools.py           (NEW: Retrieves E2B tools from the manager)
│   ├── contracts/
│   │   └── e2b_executor.py    (DELETED: Legacy E2B interface)
│   ├── services/
│   │   ├── e2b_executor.py    (DELETED: Legacy wrapper)
│   │   └── sandbox/
│   │       └── sync.py        (DELETED: Legacy sandbox sync logic)
│   ├── sandbox.py             (DELETED: Legacy monolithic sandbox execution)
│   ├── nodes/
│   │   ├── sandbox_evaluator.py (REFACTORED: Receives E2B tools via Dependency Injection)
│   │   └── qa.py              (REFACTORED: Receives E2B tools via Dependency Injection)
│   └── templates/
│       ├── QA_AUDITOR_INSTRUCTION.md (MODIFIED: Directs LLM to use run_code MCP tool)
│       └── UAT_AUDITOR_INSTRUCTION.md (MODIFIED: Directs LLM to use run_code MCP tool)
├── tests/
│   ├── unit/
│   │   ├── test_mcp_router.py (CREATED: Tests schema validation, sanitization, and context)
│   │   ├── test_sandbox_evaluator.py  (MODIFIED: Mocks injected tool dependencies)
│   │   └── test_e2b_executor.py       (DELETED/REWRITTEN: Legacy tests removed)
│   └── ac_cdd/
│       └── integration/
│           └── test_mcp_node_integration.py (CREATED: Mock E2B server integration)
```

## Design Architecture

### Pydantic Settings Design: `schemas.py`
To support robust configuration, `pydantic-settings` will validate the state before subprocess execution, reading strictly from the `.env` file.

- **`E2bMcpConfig`**: A subclass of `BaseSettings`. Enforces that `E2B_API_KEY` is present.
- **Invariants and Constraints**:
  - `E2B_API_KEY` must not be an empty string and should fail fast on instantiation if missing.
  - Generates the rigid `StdioServerParameters` with `command="npx"` and `args=["-y", "@e2b/mcp-server"]`.

### Component Design: `manager.py` & `tools.py`
- **`McpClientManager`**:
  - Uses `contextlib.asynccontextmanager` to ensure `npx` subprocesses are booted safely and cleanly terminated when the Python process shuts down, preventing zombie processes.
  - Implements an environment sanitization layer to explicitly strip `SUDO_*` variables from `os.environ` before spawning the process to prevent API key leakage via the `langchain-mcp-adapters` internal warnings.
- **Dependency Injection**: The tools are resolved at the application root (`src/cli.py` or workflow builder) and injected directly into the closures of `sandbox_evaluator.py` and `qa.py`, removing global state from the LangGraph nodes.

## Implementation Approach

1. **Infrastructure Update**:
   - Update `Dockerfile` to globally install `@e2b/mcp-server` via `npm`.
   - Update `pyproject.toml` dependencies (if missing `pydantic-settings`).
2. **Schema and Config Setup**:
   - Create `src/mcp_router/schemas.py`. Implement `E2bMcpConfig`.
3. **Manager Implementation**:
   - Create `src/mcp_router/manager.py`. Implement the `McpClientManager` as an async context manager. Implement the `SUDO_*` stripping logic.
   - Create `src/mcp_router/tools.py` to expose `get_e2b_tools()`.
4. **App Initialization & Injection**:
   - Refactor the application entry point (e.g., `src/cli.py`) to wrap graph execution inside the `McpClientManager` context. Pass the resolved `e2b_tools` to the node builders.
5. **Agent Node Refactoring**:
   - Refactor `sandbox_evaluator.py` and `qa.py` to accept the injected `e2b_tools` parameter and bind them using `llm.bind_tools(e2b_tools)`.
6. **Prompt Updates**:
   - Update `QA_AUDITOR_INSTRUCTION.md` and `UAT_AUDITOR_INSTRUCTION.md` to instruct the model to explicitly use `run_code` and `execute_command`.
7. **Legacy Cleanup**:
   - Delete all deprecated legacy files (`e2b_executor.py`, `sandbox.py`, etc.).

## Test Strategy

### Unit Testing Approach
- **Objective**: Ensure the `mcp_router` handles configuration validation, environment sanitization, and subprocess teardown safely.
- **Implementation**: Create `tests/unit/test_mcp_router.py`. Mock `StdioServerParameters`. Explicitly test `E2bMcpConfig` throwing an error if `E2B_API_KEY` is absent. Assert `SUDO_*` keys are missing from the configuration dictionary passed to `npx`. Test that the async context manager calls `close()` on the client on exit.

### Integration Testing Approach
- **Objective**: Verify that LangGraph nodes correctly utilize the injected tools and map standard LLM payloads.
- **Implementation**: Create `tests/ac_cdd/integration/test_mcp_node_integration.py`. This test relies on a dummy Node.js script mimicking `@e2b/mcp-server` over stdio.
- **Tests**:
  - `test_sandbox_evaluator_tool_binding`: Ensures the LLM emits a `ToolCall` for `run_code`.
  - `test_mcp_e2b_error_handling`: Simulates a stderr failure from the dummy script, asserting that the node correctly maps the exception payload without crashing the LangGraph execution.