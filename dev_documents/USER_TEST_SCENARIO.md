# Master Plan for User Acceptance Testing and Tutorials

## Tutorial Strategy

The primary goal of the nitpickers User Acceptance Testing (UAT) is to demonstrate the successful architectural transition from a legacy "API Wrapper" to a modern "MCP Router" model. This transformation is highly technical and largely invisible to the end-user (who interacts with the 8-cycle LangGraph workflow). Therefore, the tutorial must explicitly highlight the *robustness* and *graceful error handling* that the new `@modelcontextprotocol/server-github` and `@e2b/mcp-server` integrations provide, which were previously severe pain points.

To achieve this, the UAT strategy employs an executable, interactive Marimo notebook. This single file will guide a user through initializing the system, triggering a specific test scenario, and visually observing the LangSmith traces to confirm that the tools are being bound and executed correctly.

**Execution Modes:**
1.  **Mock Mode (CI / No-API-Key Execution):** The tutorial must be designed to run cleanly in a CI environment where real API keys (`E2B_API_KEY`, `GITHUB_PERSONAL_ACCESS_TOKEN`) might not be available or mutating real repositories is dangerous. In this mode, the `McpClientManager` is explicitly configured to connect to lightweight, local dummy Node.js servers (or mock Stdio streams) that return predefined JSON-RPC payloads mimicking the standard schemas. This proves the internal routing and state management logic functions correctly without external dependencies.
2.  **Real Mode (End-to-End Validation):** When valid API keys are provided in the `.env` file, the tutorial seamlessly switches to interacting with the real MCP servers and live cloud environments. This is intended for local developer verification to prove the end-to-end viability of the new architecture.

## Tutorial Plan

To ensure a streamlined and reproducible verification process, all UAT scenarios (from basic initialization to advanced error recovery) will be consolidated into a **SINGLE** executable Marimo file.

**Target File:** `tutorials/mcp_router_architecture_validation.py`

This notebook will be structured into the following interactive segments:

1.  **Prerequisites & Configuration Check:**
    -   Verifies the presence of required environment variables (`LANGCHAIN_TRACING_V2`, etc.).
    -   Allows the user to select between "Mock Mode" and "Real Mode" execution.
    -   Verifies the global installation of the necessary Node.js MCP server packages.
2.  **Scenario 1: The E2B Sandbox Isolation (Cycle 01 Focus):**
    -   Initializes the LangGraph engine and the `McpClientManager`.
    -   Injects a `CycleState` containing a deliberately broken Python script into the `Sandbox Evaluator` node.
    -   *Verification Objective:* Observe the LangGraph execution block and verify that the exact `stderr` from the E2B MCP server is natively captured and mapped into the `CycleState` error fields without crashing the graph.
3.  **Scenario 2: The GitHub Read-Only Fallback (Cycle 02 Focus):**
    -   Injects a `CycleState` into the `Architect` node requesting a file that does not exist in the repository.
    -   *Verification Objective:* Observe the LLM gracefully handle the standard `mcp.ServerError` natively returned via `ToolMessage` and autonomously request alternative context, proving the removal of brittle Python middleware parsing.
4.  **Scenario 3: The Mechanical Gate & Least Privilege (Cycle 03 Focus):**
    -   Forces the analytical `Auditor` node to attempt to invoke a `push_commit` ToolCall.
    -   *Verification Objective:* Explicitly verify that the LangChain execution engine rejects the invocation, demonstrating that the `McpClientManager` correctly filtered the destructive tools from the schema returned to the read-only node.

## Tutorial Validation

The `tutorials/mcp_router_architecture_validation.py` script must be completely self-contained and reproducible.

**Validation Criteria:**
-   **Execution:** The notebook must execute sequentially from top to bottom without raising unhandled exceptions.
-   **Mock Mode Isolation:** When run in Mock Mode, the script must make zero external HTTPS network calls to GitHub, E2B, or Jules.
-   **State Inspection:** The Marimo UI must clearly render the final `CycleState` dictionaries after each scenario, highlighting the specific fields where the MCP `ToolMessages` were mapped (e.g., the captured stack trace in Scenario 1).
-   **Observability:** The tutorial should output explicit links or instructions on how to view the corresponding LangSmith trace for the executed run, allowing the user to inspect the exact JSON-RPC payload routing.
