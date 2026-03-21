# Cycle 02: User Acceptance Testing (GitHub Read-Only Operations)

## Test Scenarios

### SCN-02-01: GitHub MCP Read Initialization
- **Priority**: High
- **Description**: Verify that the Node.js MCP server `@modelcontextprotocol/server-github` starts successfully via the Python `McpClientManager`.
- **User Experience**: The system initializes seamlessly with the `e2b` server, providing the architect agent with immediate file exploration capabilities.

### SCN-02-02: Native Context Gathering by Architect
- **Priority**: High
- **Description**: Verify that the LLM agent within the `Architect` node autonomously calls `get_file_content` via a `ToolCall` and successfully processes the response directly into its context window.
- **User Experience**: The agent correctly reads the `ALL_SPEC.md` without requiring explicit instructions or generating custom JSON payloads that require backend parsing.

### SCN-02-03: Graceful Fallback on Missing Files
- **Priority**: Critical
- **Description**: Verify that if the GitHub MCP server returns a `404 Not Found` error when requesting a file, the agent correctly parses the tool response, logs the error, and gracefully asks for alternative context.
- **User Experience**: When the agent requests a nonexistent file, the system handles the failure natively without crashing, allowing the LLM to recover gracefully.

### SCN-02-04: Strict Prevention of Write Operations (Security Verification)
- **Priority**: Critical
- **Description**: Ensure that the `McpClientManager` explicitly prevents any write tools (e.g., `push_commit`, `create_pull_request`) from being bound to read-only nodes (`architect.py`, `coder.py`, `auditor.py`).

## Behavior Definitions

### Feature: MCP GitHub Read-Only Context Gathering

**Scenario: System Successfully Starts the GitHub MCP Server**
- **GIVEN** a properly configured environment with a valid `GITHUB_PERSONAL_ACCESS_TOKEN`
- **WHEN** the `McpClientManager` is initialized for the `github` server
- **THEN** a background Node.js process running `@modelcontextprotocol/server-github` should start
- **AND** the list of available read-only tools (e.g., `get_file_content`, `search_repositories`) should be returned

**Scenario: Architect Successfully Gathers Context**
- **GIVEN** the Architect agent is initialized with bound GitHub read tools
- **AND** the agent's system prompt instructs it to review `ALL_SPEC.md`
- **WHEN** the agent processes the prompt
- **THEN** the model output must contain an explicit `ToolCall` for `get_file_content`
- **AND** the tool execution must return a payload containing the file's contents

**Scenario: Architect Gracefully Handles File Read Errors**
- **GIVEN** the Architect agent is initialized with bound GitHub read tools
- **AND** the agent executes a read request for a nonexistent file
- **WHEN** the MCP server returns an error execution result
- **THEN** the agent must correctly extract the error from the `ToolMessage` and continue reasoning without crashing

**Scenario: Write Tools are Explicitly Blocked**
- **GIVEN** the `McpClientManager` initialized for GitHub
- **WHEN** calling `get_github_read_tools()`
- **THEN** the returned toolset must not contain `push_commit` or `create_pull_request`