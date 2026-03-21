# Cycle 02: GitHub Read-Only Operations

## Summary
Cycle 02 focuses on migrating the context-gathering phase of the multi-agent workflow to the `@modelcontextprotocol/server-github` server. In the previous architecture, agents explicitly asked the custom Python backend for file contents by emitting custom JSON payloads, requiring dedicated parser wrappers. Now, the `architect.py`, `coder.py`, and `auditor.py` nodes will be provided injected, read-only tools natively via `.bind_tools()`. This allows the LLM to autonomously explore the repository via standard function calling (`get_file_content`, `search_repositories`), vastly improving robustness and eliminating manual prompt instructions regarding backend communication.

## System Architecture

```text
/
├── src/
│   ├── cli.py                 (MODIFIED: Injects GitHub Read tools into the graph)
│   ├── mcp_router/
│   │   ├── **schemas.py**     (MODIFIED: Adds GitHubMcpConfig via BaseSettings)
│   │   ├── **manager.py**     (MODIFIED: Handles GitHub MCP subprocess context)
│   │   └── **tools.py**       (MODIFIED: Implements specific filtering logic for read tools)
│   ├── nodes/
│   │   ├── **architect.py**   (MODIFIED: Receives injected GitHub read-only tools)
│   │   ├── **coder.py**       (MODIFIED: Receives injected GitHub read-only & E2B tools)
│   │   └── **auditor.py**     (MODIFIED: Receives injected GitHub read-only tools)
│   ├── templates/
│   │   ├── **ARCHITECT_INSTRUCTION.md** (MODIFIED: Removes manual backend file requests)
│   │   ├── **CODER_INSTRUCTION.md**     (MODIFIED: Removes manual backend file requests)
│   │   └── **AUDITOR_INSTRUCTION.md**   (MODIFIED: Removes manual backend file requests)
├── tests/
│   ├── unit/
│   │   └── **test_mcp_router.py** (MODIFIED: Tests GitHub configs and tool filtering)
│   └── ac_cdd/
│       └── integration/
│           └── **test_mcp_github_read.py** (CREATED: Tests GitHub mock integrations)
```

## Design Architecture

### Pydantic Settings Design: `schemas.py`
Extend `schemas.py` to securely configure the GitHub server.
- **`GitHubMcpConfig`**: A validated subclass of `BaseSettings` enforcing `GITHUB_PERSONAL_ACCESS_TOKEN`.
- **Invariants and Constraints**:
  - `api_key` must match basic GitHub token string lengths/formats and must not be empty. Fail fast on instantiation.
  - `command` is explicitly locked to `npx` with `["-y", "@modelcontextprotocol/server-github"]`.

### Component Design: `manager.py` & `tools.py`
- Update `McpClientManager` to asynchronously connect and terminate the GitHub client.
- `tools.py` must expose `get_github_read_tools()`. This method retrieves the complete toolset from the client and physically filters it. It returns *only* non-destructive tools (`get_file_content`, `search_repositories`, `get_issue`). Any tools related to writing (e.g., `push_commit`) must be programmatically excluded before returning the array to prevent LLM hallucination and enforce a mechanical security gate.

## Implementation Approach

1. **Schema and Config Update**:
   - Update `src/mcp_router/schemas.py` to add `GitHubMcpConfig`.
2. **Manager Extension**:
   - Update `src/mcp_router/manager.py` to handle the `@modelcontextprotocol/server-github` `stdio` connection alongside E2B. Ensure the context manager tears down both successfully.
3. **Tool Filtering Implementation**:
   - Update `src/mcp_router/tools.py` to implement `get_github_read_tools()`. Implement list comprehension filtering to explicitly block write tools.
4. **App Initialization & Injection**:
   - Update `src/cli.py` to fetch `github_read_tools` and pass them into the state graph configuration for `architect.py`, `coder.py`, and `auditor.py`.
5. **Agent Node Refactoring**:
   - Refactor `architect.py`, `coder.py`, and `auditor.py` closures to accept `github_read_tools` and bind them via `llm.bind_tools(github_read_tools)`.
6. **Prompt Updates**:
   - Update `ARCHITECT_INSTRUCTION.md`, `CODER_INSTRUCTION.md`, and `AUDITOR_INSTRUCTION.md` to instruct the LLMs to use the bound tools autonomously, removing legacy JSON payload instructions. Add explicit token mitigation directives (e.g., requesting specific line numbers when supported).

## Test Strategy

### Unit Testing Approach
- **Objective**: Ensure the `mcp_router` initializes the GitHub connection securely and `tools.py` successfully filters write capabilities.
- **Implementation**: Update `tests/unit/test_mcp_router.py`. Validate `GitHubMcpConfig`. Mock the tool response from a dummy `MultiServerMCPClient` containing both `get_file_content` and `push_commit`. Assert that `get_github_read_tools()` successfully isolates and returns *only* `get_file_content`.

### Integration Testing Approach
- **Objective**: Verify that LangGraph nodes correctly utilize the injected read tools and handle connection/file failures cleanly.
- **Implementation**: Create `tests/ac_cdd/integration/test_mcp_github_read.py`. This test relies on a mocked Node.js script mimicking the `@modelcontextprotocol/server-github` interface.
- **Tests**:
  - `test_architect_get_file_content`: Ensures `architect` natively emits a `ToolCall` for `get_file_content` and successfully processes the mocked text returned by the dummy script.
  - `test_mcp_github_read_fallback`: Simulates a `file not found` standard MCP error string returned by the mock server. Verifies the `architect.py` node traps the string, avoids JSON parsing crashes, and gracefully requests alternative context.