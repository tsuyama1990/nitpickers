# CYCLE01 SPEC: Infrastructure Preparation & E2B Sandbox Isolation

## Summary
The goal of CYCLE01 is to establish the fundamental container and dependency infrastructure required to run Model Context Protocol (MCP) servers locally, and to execute the lowest-risk migration: completely offloading dynamic sandbox code execution from custom Python wrappers to the official `@e2b/mcp-server`. This cycle is critical as it introduces the `McpClientManager`, the central routing hub that will eventually replace all legacy API middleware across the entire system. By completing this cycle, the `Sandbox Evaluator` and `QA` LangGraph nodes will transition from generating brittle JSON payloads to natively invoking standard function calls. This drastically improves the robustness of the testing loop, ensuring that complex stack traces and execution timeouts from the cloud environment are captured flawlessly and formatted correctly for the LLM without requiring manual string manipulation or rigid Pydantic models. We will also clean up and deprecate the legacy E2B service contracts.

## System Architecture
The introduction of the MCP paradigm requires a robust bridge between the Python LangGraph environment and the Node.js MCP server sidecars running concurrently within the same Docker container via the Stdio transport layer. The core architectural addition is the `src/services/mcp_client_manager.py`. This manager acts as a singleton dependency injected into the LangGraph state machine. When the `sandbox_evaluator.py` node executes, it will query the manager for the current E2B toolset. The manager communicates with the `npx @e2b/mcp-server` subprocess, retrieves the `run_code` and `execute_command` tool schemas, and LangChain binds them to the LLM. The legacy custom wrappers (`src/contracts/e2b_executor.py`, `src/services/e2b_executor.py`) are fundamentally replaced by this standard execution path. The system maintains the exact same domain data models (`CycleState`) and observability hooks (LangSmith).

```text
/
├── pyproject.toml
├── Dockerfile
├── src/
│   ├── nodes/
│   │   ├── **sandbox_evaluator.py**
│   │   └── **qa.py**
│   ├── services/
│   │   ├── **mcp_client_manager.py**   [NEW]
│   │   └── **e2b_executor.py**         [DELETED]
│   └── contracts/
│       └── **e2b_executor.py**         [DELETED]
```

## Design Architecture
This architectural refactoring relies entirely on extending our existing, highly robust Pydantic-based schemas for node definitions and tool payloads.

**Domain Concepts & Core Mappings:**
The core concept is that the execution of a tool (e.g., running a python script to test functionality) is no longer modeled as an internal Python method call that returns a custom Pydantic response. Instead, it is modeled natively as a LangChain `ToolCall` and `ToolMessage`. The `McpClientManager` handles the serialization of the LLM's raw intent into the JSON-RPC 2.0 standard required by the `@e2b/mcp-server`.

**Key Invariants & Constraints:**
1.  **Connection Pooling:** The `McpClientManager` must maintain a persistent, healthy connection to the underlying Node.js Stdio process. Re-initializing the server on every node tick is prohibited due to unacceptable latency.
2.  **Stateless Execution:** The LangGraph execution model dictates that tools must be as stateless as possible regarding the business logic. While the E2B sandbox itself holds filesystem state during a session, the Python `CycleState` must accurately reflect the *result* of the execution without implicitly relying on the sandbox's hidden context for the next transition.
3.  **Strict Error Boundaries:** The manager must enforce strict timeout configurations and catch `mcp.ClientError` or `mcp.ServerError` exceptions. These raw protocol errors must be wrapped in descriptive, context-aware Pydantic error models before being fed back into the LangGraph state, preventing the LLM from hallucinating fixes for infrastructure failures.
4.  **Backward Compatibility:** The data structure of the final output (e.g., the string content of a test failure injected into `QA_AUDITOR_INSTRUCTION.md`) must remain identical to the legacy system to ensure the overarching cycle prompts require minimal alteration.

## Implementation Approach
1.  **Dependency Updates:** First, update `pyproject.toml` to explicitly include `mcp>=1.0.0` and `langchain-mcp-adapters>=0.1.0`. Add `nodejs` installation directives to the main `Dockerfile` and pre-install `@e2b/mcp-server` globally to drastically improve container boot times.
2.  **Create McpClientManager:** Implement `src/services/mcp_client_manager.py`. Design this class to asynchronously initialize the `MultiMCPClient`. Specifically, implement the connection logic using `StdioServerParameters` targeting `npx -y @e2b/mcp-server`, securely passing the `E2B_API_KEY` from the environment.
3.  **Refactor Node Tools:** In `src/nodes/sandbox_evaluator.py` and `src/nodes/qa.py`, remove the initialization of the legacy `E2bExecutor` service. Inject the `McpClientManager`. Retrieve the tools via `await client.get_tools(server_name="e2b")`.
4.  **Bind and Execute:** Update the LangChain model invocation within the nodes to use `.bind_tools(tools)`. Ensure the system prompt clearly instructs the LLM to utilize the newly available `run_code` or `execute_command` tools.
5.  **State Transformation:** Update the node's output logic to parse the resulting `ToolMessage` (which contains the raw stdout/stderr from the E2B MCP) and correctly map it back into the persistent `CycleState` structure.
6.  **Cleanup:** Once tests pass, delete `src/contracts/e2b_executor.py` and `src/services/e2b_executor.py` entirely, ensuring no dangling imports remain.

## Test Strategy

**Unit Testing Approach:**
The primary unit testing focus will be on the newly created `src/services/mcp_client_manager.py` and the modified node logic.
-   Create `tests/unit/test_mcp_client_manager.py`. Use mocking to simulate the `mcp.StdioServerParameters` and the underlying JSON-RPC stream. Verify that the manager correctly parses the advertised tool schemas without attempting a real network connection or requiring a valid `E2B_API_KEY`.
-   Assert that the manager correctly implements timeout logic and raises appropriate, custom Pydantic-validated errors if the simulated Node.js process fails to boot or crashes unexpectedly.
-   Refactor `tests/unit/test_sandbox_evaluator.py`. Mock the `McpClientManager` to return a predefined, static schema for `run_code`. Assert that the LangGraph node successfully binds the tool and correctly formats the simulated `ToolMessage` result back into the `CycleState` without relying on legacy parsers.

**Integration Testing Approach:**
Integration testing must ensure the LangGraph nodes can communicate with a live (or locally simulated) E2B environment via the standard protocol.
-   Implement `tests/ac_cdd/integration/test_mcp_e2b_sandbox_execution.py`.
-   This test must initialize the LangGraph engine, configure the `McpClientManager` with a valid test API key (or point it at a local mock server complying with the MCP protocol), and pass a state containing a deliberately broken Python script to the `sandbox_evaluator.py` node.
-   **Crucial Assertion:** The test must verify that the execution triggers the `run_code` tool, the E2B MCP server correctly captures the `SyntaxError` from the cloud environment, and the exact `stderr` text is correctly propagated back through the `ToolMessage` into the final `CycleState`, proving the end-to-end viability of the MCP Router pattern.
