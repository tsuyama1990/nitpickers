# System Architecture: MCP Router Integration

## Summary

The nitpickers repository is fundamentally shifting its core integration architecture from a legacy "API Wrapper" approach to a modern, decentralized "MCP Router" model. This refactoring leverages the Model Context Protocol (MCP) to seamlessly and safely interact with critical external dependencies, specifically targeting GitHub (Version Control), E2B (Cloud Sandboxing), and Jules (Agent Fleet & Session Orchestration). By delegating the heavy lifting of API interaction, data formatting, tool definition schemas, and standard error handling to standardized MCP servers (sidecars), the system drastically reduces custom Python middleware overhead. The main LangGraph execution engine can now strictly focus on high-level multi-agent orchestration, resilient state transitions, and deterministic graph logic, eliminating the fragility and maintenance burden of manually mapping LLM outputs to raw REST endpoints.

## System Design Objectives

The overarching goal of this architectural transition is to dramatically simplify the maintenance footprint and increase the reliability of the nitpickers platform's external integrations. The current state relies heavily on custom Python code wrapping complex, ever-changing proprietary APIs and SDKs. This approach is intrinsically fragile; any minor upstream change breaks Pydantic validation schemas, custom JSON parsers, or hard-coded prompt injections, which cascades into catastrophic agent cycle failures.

**Primary Objectives:**
1.  **Decouple Execution from Orchestration:** Shift the responsibility of "how to execute a tool" from custom Python logic to standardized MCP servers. The Python backend (LangGraph) should exclusively focus on "when to execute" and "what to do with the result."
2.  **Eliminate Boilerplate Tool Definitions:** Remove the need to manually maintain massive Pydantic models and JSON schemas that mirror remote APIs. By dynamically resolving tools using the MCP `get_tools()` protocol, agents instantly discover the latest capabilities and schemas advertised directly by the node sidecars.
3.  **Enhance Robustness through Native LLM Support:** Utilize the LLM's native Function Calling capabilities in tandem with MCP to directly invoke tools. This bypasses brittle text-parsing middleware that historically caused crashes during unexpected API edge cases (like multi-line merge conflicts or obscure E2B timeout stack traces).
4.  **Consolidate Authentication Sprawl:** Centralize credential management. Currently, environment variables are injected piecemeal into deeply nested service classes. The MCP Client Manager will encapsulate authentication, securely passing configurations only during the Stdio initialization of the standalone MCP processes.
5.  **Preserve the 8-Cycle Workflow Integrity:** The most critical constraint is that the conceptual 8-cycle multi-agent workflow (Architect, Coder, Auditor, Master Integrator, Sandbox Evaluator, etc.) must remain undisturbed from the user's perspective. The transition must be seamless, replacing only the underlying engine without altering the high-level business logic.

**Success Criteria:**
-   Complete removal of the legacy `src/services/git/`, `src/services/jules/`, and custom `e2b` wrapper modules.
-   All agent nodes (`src/nodes/*.py`) successfully bind and execute tools directly via the new `McpClientManager`.
-   The end-to-end integration test suite passes reliably without regressions in capability.
-   Overall reduction in codebase complexity and lines of custom Python code dedicated to API management.

## System Architecture

The new architecture adopts an "MCP Router" pattern. The core Python application acts as the central router, managing a LangGraph state machine, while offloading actual operational tasks to specialized Node.js MCP server sidecars running concurrently within the same Docker environment.

**Core Components:**
1.  **LangGraph State Machine (Existing):** The orchestrator defining the workflow transitions between the various agent roles (e.g., Architect -> Coder -> Sandbox Evaluator).
2.  **MCP Client Manager (New):** A robust Python service responsible for managing the lifecycle, connection pooling, and tool discovery of the MCP servers via the Stdio transport layer. It acts as the bridge between the Python LangChain/LangGraph environment and the Node.js MCP servers.
3.  **GitHub MCP Server (`@modelcontextprotocol/server-github`):** Handles all version control operations. Bound specifically to nodes requiring repository context (Architect) or write capabilities (Master Integrator).
4.  **E2B MCP Server (`@e2b/mcp-server`):** Manages ephemeral cloud sandboxing, bash command execution, and code evaluation. Bound to nodes like Sandbox Evaluator and QA.
5.  **Jules MCP Server (`@google/jules-mcp`):** Orchestrates dynamic agent fleets and complex parallel session reconciliations. Bound to high-level orchestration nodes.

**Data Flow:**
1.  The LangGraph engine transitions to an agent node (e.g., Coder).
2.  The node requests available tools from the `MCP Client Manager`.
3.  The manager queries the respective MCP servers (via JSON-RPC over Stdio) and returns the native tool schemas.
4.  The tools are bound to the LLM via `.bind_tools()`.
5.  The LLM decides to invoke a tool (e.g., `execute_command`).
6.  The invocation is routed through the `MCP Client Manager` to the E2B MCP server.
7.  The Node.js server executes the raw command securely in the cloud.
8.  The execution result (stdout/stderr) is formatted natively by the server and returned through the router directly into the LLM's context window.

**Boundary Management and Separation of Concerns:**
-   **Strict Principle of Least Privilege:** Read-only nodes (like the Architect) must only be bound to safe, read-only tools exposed by the MCP manager (e.g., `get_file_content`). Write-enabled nodes (like the Master Integrator) are the only entities permitted to bind destructive tools (e.g., `push_commit`). This enforces mechanical gates at the graph level.
-   **Zero State Intermingling:** The MCP servers must remain completely stateless regarding the overarching 8-cycle business logic. They simply execute discrete commands. State persistence (like `project_state.json`) remains strictly within the domain of the existing Python `state_manager.py`.

```mermaid
graph TD
    subgraph Core System [Python LangGraph Application]
        direction TB
        SM[State Manager]
        CM[MCP Client Manager]
        N_Arch[Architect Node]
        N_Code[Coder Node]
        N_Eval[Sandbox Evaluator Node]
        N_Integ[Master Integrator Node]

        N_Arch --> CM
        N_Code --> CM
        N_Eval --> CM
        N_Integ --> CM

        SM -.-> N_Arch
        SM -.-> N_Code
    end

    subgraph MCP Servers [Node.js Sidecars via Stdio]
        MCP_GH[@modelcontextprotocol/server-github]
        MCP_E2B[@e2b/mcp-server]
        MCP_Jules[@google/jules-mcp]
    end

    CM <-->|JSON-RPC via Stdio| MCP_GH
    CM <-->|JSON-RPC via Stdio| MCP_E2B
    CM <-->|JSON-RPC via Stdio| MCP_Jules

    MCP_GH <-->|HTTPS| GH_API[GitHub API]
    MCP_E2B <-->|HTTPS| E2B_Cloud[E2B Cloud Sandboxes]
    MCP_Jules <-->|HTTPS| Jules_Fleet[Jules Agent Fleet]
```

## Design Architecture

The architectural refactoring is designed to maximize the reuse of the existing core Pydantic domain models governing the 8-cycle state transitions, while aggressively pruning the legacy service layers responsible for network operations. The fundamental structures defining `CycleState`, `AgentMessage`, and validation schemas remain intact, ensuring backward compatibility with the existing observability and persistence layers.

**File Structure Overview:**
```text
/src
├── domain_models/       (Unchanged: Core state definitions)
├── nodes/               (Modified: Updated to bind MCP tools dynamically)
│   ├── architect.py
│   ├── coder.py
│   ├── sandbox_evaluator.py
│   └── master_integrator.py
├── services/            (Heavily Modified: Deletions and Replacements)
│   ├── git/             [TO BE DELETED]
│   ├── jules/           [TO BE DELETED]
│   ├── e2b_executor.py  [TO BE DELETED]
│   └── mcp_client_manager.py [NEW: Central Router]
├── graph.py             (Unchanged: High-level routing logic)
└── state_manager.py     (Unchanged: Persistence logic)
```

**Core Domain Pydantic Models & Extensibility:**
The existing system relies on rigorous Pydantic models, such as `CycleState`, which enforces strict invariants (e.g., `cycle_id` must be exactly two digits, validation rules on status transitions). The new MCP integration does not require altering these core domain models. Instead, it alters the *payload execution mechanisms* within the LangGraph nodes.

When an agent needs to record an action, it still mutates the `CycleState`. The distinction is that instead of calling a monolithic Python wrapper (e.g., `git_ops.push()`) and waiting for a massive Pydantic response object that requires parsing, the agent natively receives a standardized `ToolMessage` from LangChain following the MCP execution.

**Key Invariants:**
-   **Stateless Operations:** All MCP tool executions must be treated as stateless actions. The Python graph must not assume that the E2B sandbox retains state between independent agent turns unless explicitly managed by the graph's context.
-   **Fallback Gracefulness:** The `MCP Client Manager` must implement robust connection pooling and retry logic for the Stdio server initializations. If a sidecar fails to boot, the manager must raise a clear exception caught by the LangGraph error boundary, preventing silent failures.

## Implementation Plan

The project will be executed in three distinct, sequential cycles to minimize risk and ensure continuous stability. This phased approach, the "strangler fig pattern," replaces legacy components domain by domain, verifying integrity via the existing test suite before proceeding.

### CYCLE01: Infrastructure Preparation & E2B Sandbox Isolation
This foundational cycle establishes the required container infrastructure and tackles the lowest-risk, highest-yield migration: offloading sandbox execution to the E2B MCP.
-   Update `Dockerfile` to install the Node.js runtime and globally install the necessary MCP server npm packages.
-   Update `pyproject.toml` with the required Python adapters (`mcp`, `langchain-mcp-adapters`).
-   Implement the `MCP Client Manager` (`src/services/mcp_client_manager.py`) to handle the sequential booting and lifecycle management of the Stdio processes.
-   Refactor `src/nodes/sandbox_evaluator.py` and `QA` nodes to bind the E2B MCP tools instead of generating custom payload requests.
-   Delete the legacy `src/contracts/e2b_executor.py` and `src/services/e2b_executor.py`.

### CYCLE02: GitHub Read-Only Operations Transition
This cycle focuses on transitioning the analytical, read-heavy operations, effectively reducing the token bloat and fragility associated with custom file-reading wrappers.
-   Configure the `MCP Client Manager` to initialize `@modelcontextprotocol/server-github`.
-   Identify read-only capabilities (e.g., `get_file_content`, `search_repositories`) exposed by the GitHub MCP.
-   Refactor the `Architect` and `Auditor` nodes (`src/nodes/architect.py`, etc.) to bind these specific read-only tools.
-   Update system prompts (e.g., `ARCHITECT_INSTRUCTION.md`) to instruct the LLM to autonomously utilize these tools for codebase exploration rather than requesting context from the Python middleware.

### CYCLE03: GitHub Write Operations & Jules Orchestration Migration
The final, most critical cycle replaces the complex orchestration of Git state modifications and parallel agent dispatching, finalizing the removal of all legacy wrapper APIs.
-   Refactor the `Master Integrator` node (`src/nodes/master_integrator.py`) to utilize the destructive write tools from the GitHub MCP natively (e.g., `create_pull_request`, `push_commit`).
-   Connect the `MCP Client Manager` to `@google/jules-mcp`.
-   Refactor the `Global Refactor` and `Audit Orchestrator` nodes to dispatch dynamic fleets via the Jules MCP tools.
-   Conduct the final, complete deletion of the massive legacy directory trees: `src/services/git/` and `src/services/jules/`.

## Test Strategy

To ensure safe migration without breaking the highly stable 8-cycle architecture, rigorous testing must accompany each phase. The strategy mandates the use of isolated environments and mock structures to prevent accidental mutations during development.

### CYCLE01 Test Strategy (E2B Isolation)
-   **Unit Tests:** Develop `tests/unit/test_mcp_client_manager.py` to rigorously test the lifecycle management. Mock the `StdioServerParameters` to verify that the `MultiMCPClient` correctly discovers tools from a simulated stream without real network calls. Ensure boot timeout exceptions are correctly raised and handled. Rewrite `test_sandbox_evaluator.py` to assert correct `.bind_tools()` application.
-   **Integration/E2E Tests:** Execute the existing end-to-end tests against the refactored evaluator. Ensure that when the sandbox evaluator is forced to run a deliberately broken script, the E2B MCP tool correctly captures the `stderr` exception and feeds it back into the graph, accurately categorizing the failure without breaking the parsing logic.

### CYCLE02 Test Strategy (GitHub Read-Only)
-   **Unit Tests:** Verify the principle of least privilege. Write tests explicitly checking that the `Architect` node's initialization routine only binds safe, read-only tools and structurally rejects any write-access capabilities.
-   **Integration Tests:** Implement `test_mcp_github_read_fallback()`. Simulate a scenario using an interceptor where `get_file_content` returns a "file not found" error natively from the MCP server. Assert that the `Architect` node gracefully handles the standardized JSON-RPC error response and requests alternative context, rather than crashing on an unexpected exception format.

### CYCLE03 Test Strategy (GitHub Write & Jules Dispatch)
-   **Integration Tests:** This phase demands rigorous robustness testing. Utilize `tests/ac_cdd/integration/test_git_robustness.py`. Point the system at a secure, isolated dummy repository. Assert that complex branching logic, merge conflict resolutions, and PR creations function flawlessly end-to-end using the new MCP route.
-   **E2E Fleet Testing:** Execute `test_mcp_jules_session_dispatch()`. Trigger a massive, repository-wide refactor requiring the `Global Refactor` node. Assert that the Jules MCP correctly dispatches multiple parallel workers, tracks their sessions, and returns reconciled diffs without dropping the LangGraph state. Use LangSmith traces to explicitly verify the structure of the multi-modal API payloads routed through the new MCP manager.
