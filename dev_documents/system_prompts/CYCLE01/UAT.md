# CYCLE01 UAT: Infrastructure Preparation & E2B Sandbox Isolation

## Test Scenarios

| Scenario ID | Priority | Description |
| :--- | :--- | :--- |
| UAT-C01-01 | High | Verify the `McpClientManager` successfully initializes the `@e2b/mcp-server` process via Stdio and exposes the `run_code` and `execute_command` tools to the LangGraph node context. |
| UAT-C01-02 | Critical | Verify the `Sandbox Evaluator` accurately executes a simple Python script in the E2B cloud using the MCP tool and retrieves the correct standard output without legacy API middleware. |
| UAT-C01-03 | Critical | Verify that syntax errors or execution timeouts within the E2B cloud environment are accurately captured by the MCP server and mapped correctly into the `CycleState` error fields. |

## Behavior Definitions

**Scenario UAT-C01-01: Tool Discovery via Stdio Protocol**
*   **GIVEN** the application is properly configured with an `E2B_API_KEY` and the Node.js runtime is installed in the local environment
*   **WHEN** the `McpClientManager` is initialized asynchronously
*   **THEN** the manager must successfully connect to the `@e2b/mcp-server` sidecar process
*   **AND** the manager must return a valid list of LangChain-compatible tools including `run_code` and `execute_command`.

**Scenario UAT-C01-02: Native Code Execution via Tool Binding**
*   **GIVEN** the `Sandbox Evaluator` node is initialized within the LangGraph state machine with the E2B MCP tools bound to the LLM
*   **WHEN** the node receives a `CycleState` containing a valid Python script that prints "Hello, MCP World!"
*   **THEN** the LLM must natively invoke the `run_code` tool via a `ToolCall`
*   **AND** the E2B MCP server must securely execute the code in the cloud sandbox
*   **AND** the exact string "Hello, MCP World!" must be returned via a `ToolMessage` and recorded in the updated `CycleState`.

**Scenario UAT-C01-03: Robust Error Capture and State Mapping**
*   **GIVEN** the `Sandbox Evaluator` node is initialized with the E2B MCP tools bound
*   **WHEN** the node receives a `CycleState` containing a deliberately broken Python script (e.g., `print(1/0)`)
*   **THEN** the LLM must natively invoke the `run_code` tool
*   **AND** the E2B MCP server must execute the code and capture the resulting `ZeroDivisionError`
*   **AND** the standard error output (`stderr`) containing the Python traceback must be successfully parsed from the `ToolMessage`
*   **AND** the error details must be explicitly mapped to the failure categorization fields within the persistent `CycleState`, preventing the agent from hallucinating a successful execution.
