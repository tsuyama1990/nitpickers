# CYCLE02 UAT: GitHub Read-Only Operations Transition

## Test Scenarios

| Scenario ID | Priority | Description |
| :--- | :--- | :--- |
| UAT-C02-01 | High | Verify the `McpClientManager` successfully connects to the `@modelcontextprotocol/server-github` sidecar process and retrieves the correct read-only tools while filtering out destructive write tools. |
| UAT-C02-02 | Critical | Verify the `Architect` node correctly queries the repository for file contents natively using the `get_file_content` tool, and that the returned payload is securely paginated and truncated by the proxy layer to prevent token exhaustion. |
| UAT-C02-03 | Critical | Verify that the analytical nodes securely handle "File Not Found" errors natively returned by the GitHub MCP Server via `ToolMessage` without crashing the graph state. |

## Behavior Definitions

**Scenario UAT-C02-01: Secure Tool Filtering via Principle of Least Privilege**
*   **GIVEN** the application is properly configured with a `GITHUB_PERSONAL_ACCESS_TOKEN`
*   **WHEN** the `Architect` node requests read-only tools from the `McpClientManager`
*   **THEN** the manager must successfully return the `get_file_content` and `search_repositories` tools
*   **AND** the manager must strictly omit the `push_commit`, `create_branch`, or `create_pull_request` tools from the returned schema
*   **AND** the read-only tools must be successfully bound to the LLM.

**Scenario UAT-C02-02: Native Repository Exploration with Pagination Proxies**
*   **GIVEN** the `Architect` node is initialized within the LangGraph state machine with the proxied GitHub read-only MCP tools bound
*   **WHEN** the node requests the contents of a massively large file (e.g., a 100,000 character minified bundle)
*   **THEN** the LLM must autonomously invoke the `get_file_content` tool via a `ToolCall`
*   **AND** the GitHub MCP server fetches the file
*   **AND** the `McpClientManager` proxy layer must intervene and truncate the payload to the safe predefined character limit
*   **AND** the securely truncated file contents must be returned via a `ToolMessage` and populated in the LLM context window without crashing the graph state.

**Scenario UAT-C02-03: Graceful Error Handling and Recovery**
*   **GIVEN** the `Architect` node is initialized with the GitHub read-only tools bound
*   **WHEN** the node autonomously invokes the `get_file_content` tool requesting a deliberately non-existent file path
*   **THEN** the GitHub MCP server must return a standardized JSON-RPC error response indicating "File Not Found"
*   **AND** the error must be correctly formatted within a `ToolMessage` and returned to the LLM natively
*   **AND** the LangGraph execution must not crash with a fatal exception, allowing the LLM to gracefully acknowledge the missing file and request alternative context.
