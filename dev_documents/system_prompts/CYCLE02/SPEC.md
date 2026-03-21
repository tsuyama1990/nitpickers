# Cycle 02: GitHub Read-Only Operations

## Summary
Cycle 02 focuses on migrating the context-gathering phase of the multi-agent workflow to the `@modelcontextprotocol/server-github` server. In the previous architecture, agents explicitly asked the custom Python backend for file contents by emitting custom JSON payloads, requiring dedicated parser wrappers. Now, the `architect.py`, `coder.py`, and `auditor.py` nodes will be provided read-only tools natively via `.bind_tools()`. This allows the LLM to autonomously explore the repository via standard function calling (`get_file_content`, `search_repositories`), vastly improving robustness and eliminating manual prompt instructions regarding backend communication.

## System Architecture

```text
/
├── src/
│   ├── domain_models/
│   │   └── **mcp_schema.py**      (MODIFIED: Adds GitHub read-only config types)
│   ├── **mcp_client_manager.py**  (MODIFIED: Handles GitHub MCP connections)
│   ├── nodes/
│   │   ├── **architect.py**       (MODIFIED: Binds GitHub read-only tools)
│   │   ├── **coder.py**           (MODIFIED: Binds GitHub read-only & E2B tools)
│   │   └── **auditor.py**         (MODIFIED: Binds GitHub read-only tools)
│   ├── templates/
│   │   ├── **ARCHITECT_INSTRUCTION.md** (MODIFIED: Removes manual backend file requests)
│   │   ├── **CODER_INSTRUCTION.md**     (MODIFIED: Removes manual backend file requests)
│   │   └── **AUDITOR_INSTRUCTION.md**   (MODIFIED: Removes manual backend file requests)
├── tests/
│   ├── unit/
│   │   └── **test_mcp_client_manager.py** (MODIFIED: Tests GitHub configs)
│   └── ac_cdd/
│       └── integration/
│           └── **test_mcp_github_read.py** (CREATED: Tests GitHub mock integrations)
```

## Design Architecture

### Pydantic Schema Design: `mcp_schema.py`
Extend the existing `mcp_schema.py` (created in Cycle 01) to support GitHub.
- **`GitHubMcpConfig`**: A validated Pydantic model enforcing that the `GITHUB_PERSONAL_ACCESS_TOKEN` is present in the environment.
- **Invariants and Constraints**:
  - `api_key` must match basic GitHub token patterns.
  - `command` is set to `npx` with strict arguments `["-y", "@modelcontextprotocol/server-github"]`.
- **Consumers**: `McpClientManager` consumes this configuration to instantiate the GitHub connections.

### Component Design: `mcp_client_manager.py`
- Extend the manager to initialize the `@modelcontextprotocol/server-github` via a new async method `get_github_read_tools()`.
- Explicitly map only read-capable tools (e.g., `get_file_content`, `search_repositories`, `get_issue`) to return to the `architect.py`, `coder.py`, and `auditor.py` nodes. Write tools must be strictly filtered out to prevent hallucinated changes at this stage.

## Implementation Approach

1. **Schema and Config Update**:
   - Update `src/domain_models/mcp_schema.py` to add `GitHubMcpConfig`.
2. **Manager Extension**:
   - Update `src/mcp_client_manager.py` to initialize the `@modelcontextprotocol/server-github` connection and implement `get_github_read_tools()` that returns only non-destructive reading capabilities.
3. **Agent Node Refactoring**:
   - Refactor `src/nodes/architect.py`, `src/nodes/coder.py`, and `src/nodes/auditor.py` to instantiate the `McpClientManager`, call `get_github_read_tools()`, and bind them via `.bind_tools()`.
4. **Prompt Updates**:
   - Update the system prompts (`ARCHITECT_INSTRUCTION.md`, `CODER_INSTRUCTION.md`, `AUDITOR_INSTRUCTION.md`) to instruct the LLMs to use the bound tools autonomously to fetch file contents, removing legacy JSON payload instructions. Add specific instructions to mitigate token exhaustion (e.g., reading specific line numbers or chunks when possible, though initial testing will rely on standard `get_file_content`).

## Test Strategy

### Unit Testing Approach
- **Objective**: Ensure `McpClientManager` initializes the GitHub connection correctly and correctly filters out write tools.
- **Implementation**: Update `tests/unit/test_mcp_client_manager.py`. Mock the `StdioServerParameters` and assert that `get_github_read_tools()` only returns functions like `get_file_content` and explicitly excludes tools like `push_commit`. Test the validation of `GitHubMcpConfig`.

### Integration Testing Approach
- **Objective**: Verify that LangGraph nodes correctly bind GitHub read tools and that context generation gracefully handles read failures.
- **Implementation**: Create `tests/ac_cdd/integration/test_mcp_github_read.py`. This test will implement a lightweight, dummy Node.js script mimicking the `@modelcontextprotocol/server-github` interface.
- **Tests**:
  - `test_architect_get_file_content`: Ensures that the `architect` node natively uses `get_file_content` via a `ToolCall` and successfully processes the mocked file content returned by the server.
  - `test_mcp_github_read_fallback`: Simulates a `file not found` error returned by the mock server. Verifies that the `architect.py` node correctly processes the error string and requests alternative context without crashing the LangGraph execution.