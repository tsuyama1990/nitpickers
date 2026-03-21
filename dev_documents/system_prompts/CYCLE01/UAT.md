# Cycle 01: User Acceptance Testing (E2B Sandbox Isolation)

## Test Scenarios

### SCN-01-01: Initialization of MCP Environment
- **Priority**: High
- **Description**: Verify that the Node.js MCP server `@e2b/mcp-server` starts successfully via the Python `McpClientManager` without crashing or throwing subprocess timeout errors.
- **User Experience**: The system initializes rapidly, downloading tools asynchronously from the stdio pipe, making the platform ready for execution instantly.

### SCN-01-02: Native Tool Binding in QA Node
- **Priority**: High
- **Description**: Verify that the LLM agent within the `QA` node natively outputs a `ToolCall` directed at the E2B server rather than attempting to emit legacy JSON payloads in the message body.
- **User Experience**: The agent correctly invokes `run_code` on the sandbox, successfully executing a Python script provided in its context window and correctly capturing standard output.

### SCN-01-03: Graceful Failure Handling in Sandbox Evaluator
- **Priority**: Critical
- **Description**: Verify that if the E2B MCP server returns an error or stderr string from a faulty script execution, the agent correctly parses the tool response, captures the error, and categorizes the failure correctly in its output plan.
- **User Experience**: When the generated code crashes, the system handles the `stderr` natively, and the auditor loops back to correctly instruct the coder to fix the error.

### SCN-01-04: API Key Leakage Prevention (Security Verification)
- **Priority**: Critical
- **Description**: Ensure that the `McpClientManager` sanitizes `os.environ` before spawning the Node.js process, specifically filtering out `SUDO_*` environment variables, ensuring no API keys are logged or passed inappropriately to external sidecars.

## Behavior Definitions

### Feature: MCP E2B Sandbox Execution

**Scenario: System Successfully Starts the E2B MCP Server**
- **GIVEN** a properly configured environment with a valid `E2B_API_KEY`
- **WHEN** the `McpClientManager` is initialized for the `e2b` server
- **THEN** a background Node.js process running `@e2b/mcp-server` should start
- **AND** the `MultiMCPClient` should successfully connect via `stdio`
- **AND** the list of available tools (e.g., `run_code`, `execute_command`) should be returned

**Scenario: Agent Successfully Invokes Code Execution**
- **GIVEN** the QA agent is initialized with bound E2B tools
- **AND** the agent's system prompt instructs it to evaluate a valid Python file
- **WHEN** the agent processes the prompt
- **THEN** the model output must contain an explicit `ToolCall` for `run_code`
- **AND** the tool execution must return a payload containing the script's `stdout`

**Scenario: Agent Gracefully Handles Script Errors**
- **GIVEN** the Sandbox Evaluator agent is initialized with bound E2B tools
- **AND** the agent executes a script containing a syntax error via the E2B MCP
- **WHEN** the MCP server returns the `stderr` execution result
- **THEN** the agent must not crash due to JSON parsing failures
- **AND** the agent must correctly extract the traceback from the `ToolMessage` and mark the evaluation state as `FAILED`

**Scenario: Environment Initialization Sanitizes Credentials**
- **GIVEN** an environment containing injected secrets in a `SUDO_COMMAND` variable
- **WHEN** the `McpClientManager` initializes the `e2b` MCP connection
- **THEN** the internal subprocess configuration must not contain any `SUDO_*` keys
- **AND** no `SUDO_*` keys should be present in the execution logs or tool responses