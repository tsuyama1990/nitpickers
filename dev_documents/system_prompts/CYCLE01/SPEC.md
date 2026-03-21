# Cycle 01: E2B Sandbox Isolation

## Summary
Cycle 01 is the foundational phase for transitioning the Nitpickers application from a rigid API Wrapper architecture to a modern MCP Router paradigm. The primary focus of this cycle is to introduce the necessary Node.js infrastructure for Model Context Protocol (MCP) servers and migrate all E2B Cloud Sandboxing interactions to the `@e2b/mcp-server`. This migration targets the `sandbox_evaluator` and `qa` nodes, transitioning them to natively use function calling to execute code and test environments securely. By delegating all bash environment interactions and evaluations to the MCP server, we eliminate custom Python wrappers, manual error parsing, and brittle context injection related to the E2B SDK, resulting in a cleaner, highly deterministic execution environment for the LLM.

## System Architecture

In this cycle, we introduce the base `McpClientManager`, which connects to the `@e2b/mcp-server` over `stdio`. LangGraph nodes `sandbox_evaluator.py` and `qa.py` will dynamically pull these E2B tools.

```text
/
├── Dockerfile                 (MODIFIED: Adds Node.js & @e2b/mcp-server)
├── pyproject.toml             (MODIFIED: Adds mcp and langchain-mcp-adapters)
├── src/
│   ├── domain_models/
│   │   └── **mcp_schema.py**      (CREATED: E2B connection parameters & types)
│   ├── **mcp_client_manager.py**  (CREATED: Handles MultiMCPClient & StdioServerParameters)
│   ├── contracts/
│   │   └── e2b_executor.py    (DELETED: Legacy E2B interface)
│   ├── services/
│   │   ├── e2b_executor.py    (DELETED: Legacy wrapper)
│   │   └── sandbox/
│   │       └── sync.py        (DELETED: Legacy sandbox sync logic)
│   ├── sandbox.py             (DELETED: Legacy monolithic sandbox execution)
│   ├── nodes/
│   │   ├── **sandbox_evaluator.py** (MODIFIED: Binds E2B MCP tools natively)
│   │   └── **qa.py**              (MODIFIED: Binds E2B MCP tools natively)
│   └── templates/
│       ├── **QA_AUDITOR_INSTRUCTION.md** (MODIFIED: Directs LLM to use run_code MCP tool)
│       └── **UAT_AUDITOR_INSTRUCTION.md** (MODIFIED: Directs LLM to use run_code MCP tool)
├── tests/
│   ├── unit/
│   │   ├── **test_mcp_client_manager.py** (CREATED)
│   │   ├── test_sandbox_evaluator.py  (MODIFIED: Mocked MCP connection)
│   │   └── test_e2b_executor.py       (DELETED/REWRITTEN: Legacy tests removed)
│   └── ac_cdd/
│       └── integration/
│           └── **test_mcp_node_integration.py** (CREATED: Mock E2B server integration)
```

## Design Architecture

### Pydantic Schema Design: `mcp_schema.py`
To support the connection between the main Python service and the external Node.js MCP processes, robust Pydantic schemas will validate the configuration state before subprocess execution.

- **`E2BMcpConfig`**: A strictly validated Pydantic model enforcing that the `E2B_API_KEY` is present and valid in the environment. It also validates the base configuration for `StdioServerParameters`.
- **Invariants and Constraints**:
  - `api_key` must not be an empty string and should match basic security regex patterns.
  - `command` is rigidly set to `npx` with strict arguments `["-y", "@e2b/mcp-server"]`.
- **Consumers**: `McpClientManager` consumes this configuration to instantiate the connections safely.
- **Extensibility**: Designed to be subclassed or composed alongside future GitHub and Jules configuration schemas in subsequent cycles.

### Component Design: `mcp_client_manager.py`
- Implements a Singleton or Dependency-Injected `MultiServerMCPClient`.
- Features built-in environment sanitization to prevent API key leakage (specifically filtering out `SUDO_*` environment variables prior to passing `os.environ` to `npx`).
- Provides a unified `get_e2b_tools()` async method to yield the LangChain-compatible `BaseTool` abstractions for node injection.

## Implementation Approach

1. **Infrastructure Update**:
   - Update `Dockerfile` to install Node.js (via nodesource setup) and globally install `@e2b/mcp-server` to lock versions and prevent runtime downloads.
   - Update `pyproject.toml` to add `mcp` and `langchain-mcp-adapters`. Run `uv sync`.
2. **Schema and Config Setup**:
   - Create `src/domain_models/mcp_schema.py` and implement the strict Pydantic configurations for the E2B client.
3. **Manager Implementation**:
   - Create `src/mcp_client_manager.py`. Implement an async initialization method using `StdioServerParameters`. Crucially, implement the logic to sanitize `os.environ` to strip `SUDO_*` variables before passing them to the subprocess.
4. **Agent Node Refactoring**:
   - Refactor `src/nodes/sandbox_evaluator.py` and `src/nodes/qa.py` to instantiate the `McpClientManager`, call `get_e2b_tools()`, and bind them to the specific `llm` via `.bind_tools()`.
5. **Prompt Updates**:
   - Update the system prompts (`QA_AUDITOR_INSTRUCTION.md`, `UAT_AUDITOR_INSTRUCTION.md`) to instruct the model to explicitly use the bound `run_code` and `execute_command` tools instead of emitting custom JSON payloads.
6. **Legacy Cleanup**:
   - Delete all deprecated legacy files (`src/contracts/e2b_executor.py`, `src/services/e2b_executor.py`, `src/sandbox.py`, `src/services/sandbox/sync.py`).

## Test Strategy

### Unit Testing Approach
- **Objective**: Ensure `McpClientManager` initializes correctly without external side-effects and parses schema correctly.
- **Implementation**: Create `tests/unit/test_mcp_client_manager.py`. Mock the `StdioServerParameters` and `MultiServerMCPClient.connect` to verify that environment variables (especially the `SUDO_*` sanitization logic) are correctly applied. Test the Pydantic schemas in `mcp_schema.py` explicitly for validation failures on empty API keys.
- **Environment Rules**: Ensure all unit tests run completely offline and use strictly mocked `e2b` parameters.

### Integration Testing Approach
- **Objective**: Verify that LangGraph nodes correctly bind tools and that the LLM payload maps accurately to the expected tool calls.
- **Implementation**: Create `tests/ac_cdd/integration/test_mcp_node_integration.py`. This test will implement a lightweight, dummy Node.js script that simply mimics the `@e2b/mcp-server` interface over stdio.
- **Tests**:
  - `test_sandbox_evaluator_tool_binding`: Ensures that when `sandbox_evaluator` receives a prompt requiring code execution, the LLM emits a native `ToolCall` for `run_code`.
  - `test_mcp_e2b_sandbox_execution_error_handling`: Simulates a dummy script that throws stderr via the mock server, asserting that the node correctly traps the exception and feeds the stderr back into the graph state.