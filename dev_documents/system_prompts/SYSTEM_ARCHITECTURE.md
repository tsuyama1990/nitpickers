# System Architecture

## Summary
The Nitpickers platform is transitioning from a legacy "API Wrapper" architecture to a modern "MCP Router" paradigm. Historically, the Python backend manually wrapped external API calls (e.g., GitHub, E2B, Jules), creating brittle interdependencies and requiring continuous manual updates to prompt schemas and response parsers. The new architecture integrates the Model Context Protocol (MCP) using standalone Node.js sidecar servers. This allows Large Language Model (LLM) agents to natively invoke standardized tools via JSON-RPC 2.0. By decoupling the LLM from underlying API mechanics, the core Python application focuses entirely on multi-agent orchestration, state management, and LangGraph logic.

## System Design Objectives
The primary objectives of this architectural shift are to reduce maintenance overhead, eliminate technical debt, and significantly improve the robustness of the 8-cycle multi-agent workflow.

1. **Decoupling and Standardization:** Transition the application from a rigid API Wrapper to an MCP Router. This offloads tool execution, payload formatting, authentication, and error handling to standardized, vendor-maintained MCP servers (GitHub, E2B, Jules).
2. **Native LLM Tool Calling:** Leverage the built-in function-calling capabilities of modern LLMs. MCP servers will advertise their available tools, semantic descriptions, and strongly-typed required schemas directly to the LLM upon initialization.
3. **Resilience and Determinism:** Eliminate the fragility associated with custom parsers breaking on edge-case API responses (e.g., Git merge conflicts, E2B timeout stack traces). The MCP servers will execute operations securely and return natively formatted context payloads back to the LLMs.
4. **Seamless Integration:** The architectural transition must strictly preserve the existing 8-cycle workflow from the user's perspective. No changes will be made to the fundamental user experience, state persistence (e.g., `project_state.json`), or out-of-scope external tools (like web search).
5. **Secure Execution:** API keys and sensitive environment variables will be securely managed and routed only to the specific MCP subprocesses that require them, reducing authentication sprawl across the Python codebase.

## System Architecture
The new system architecture introduces three standalone Node.js MCP Server sidecars (`@modelcontextprotocol/server-github`, `@e2b/mcp-server`, `@google/jules-mcp`) communicating with the main Python application via the `stdio` transport layer.

- **MCP Client Manager (`src/mcp_client_manager.py`):** A newly introduced core component responsible for the lifecycle of the MCP subprocesses. It securely loads credentials, manages concurrent connection pooling, and exposes standardized `get_tools()` interfaces to dynamic agent nodes.
- **LangGraph Agents:** The existing LangGraph nodes (e.g., Coder, Auditor, Master Integrator, Sandbox Evaluator) will be heavily refactored. They will dynamically bind to the tools exposed by the MCP Client Manager using `.bind_tools()`.
- **Explicit Boundary Management:** Write tools (e.g., `push_commit`, `create_pull_request`) are strictly constrained to write-enabled nodes like the Master Integrator. Read-only nodes (e.g., Architect) will only receive read-only tools.

```mermaid
graph TD
    subgraph Observability Layer [LangSmith Observability]
        direction TB
        TR[Tracer & State Logger]
    end

    subgraph MCP Sidecars [Node.js MCP Servers via stdio]
        G_MCP[@modelcontextprotocol/server-github]
        E_MCP[@e2b/mcp-server]
        J_MCP[@google/jules-mcp]
    end

    subgraph Core Python Backend [MCP Router via LangGraph]
        MCM[MCP Client Manager]
        MCM -->|stdio| G_MCP
        MCM -->|stdio| E_MCP
        MCM -->|stdio| J_MCP

        subgraph Agents [LangGraph Nodes]
            C[Coder Agent]
            A[Auditor Agent]
            MI[Master Integrator]
            SE[Sandbox Evaluator]
        end

        Agents -->|bind_tools| MCM
    end

    subgraph External APIs
        GitHub[GitHub API]
        E2B[E2B Cloud Sandboxes]
        Jules[Jules Fleet]
    end

    G_MCP --> GitHub
    E_MCP --> E2B
    J_MCP --> Jules

    TR -.-> Agents
    TR -.-> MCM
```

## Design Architecture
The file structure and component design reflect the transition from custom services to standard MCP integrations.

```text
/
├── dev_documents/
│   ├── ALL_SPEC.md
│   ├── USER_TEST_SCENARIO.md
│   └── system_prompts/
│       ├── SYSTEM_ARCHITECTURE.md
│       ├── CYCLE01/
│       ├── CYCLE02/
│       └── CYCLE03/
├── src/
│   ├── cli.py
│   ├── domain_models/
│   │   ├── mcp_schema.py      (NEW: Defines MCP connection parameters & strict types)
│   │   └── project_state.py   (EXISTING: Kept as-is for state persistence)
│   ├── mcp_client_manager.py  (NEW: Lifecycle manager for MCP sidecars)
│   ├── nodes/
│   │   ├── architect.py       (REFACTORED: Binds to read-only GitHub MCP tools)
│   │   ├── auditor.py         (REFACTORED: Binds to read-only tools)
│   │   ├── coder.py           (REFACTORED: Binds to E2B and read-only GitHub MCP tools)
│   │   ├── master_integrator.py (REFACTORED: Binds to GitHub write MCP tools)
│   │   └── sandbox_evaluator.py (REFACTORED: Binds strictly to E2B MCP tools)
│   └── templates/             (REFACTORED: System prompts updated to utilize tool calling natively)
├── tests/
│   ├── unit/
│   │   └── test_mcp_client_manager.py
│   └── ac_cdd/
│       └── integration/
│           ├── test_mcp_node_integration.py
│           └── test_end_to_end_workflow.py
├── pyproject.toml
├── Dockerfile                 (REFACTORED: Adds Node.js runtime and global MCP servers)
└── docker-compose.yml
```

### Core Domain Pydantic Models Structure and Typing
The existing `domain_models` will be extended with `mcp_schema.py`. This new schema file will define robust Pydantic models for configuration parameters required by the `McpClientManager`.
- `McpServerConfig`: Validates environment variables (e.g., `GITHUB_PERSONAL_ACCESS_TOKEN`, `E2B_API_KEY`) and server commands (`npx`).
- Existing objects like `CycleState` and `ProjectManifest` remain untouched, ensuring the state tracker does not require an overhaul. The new models integrate purely to configure the MCP environment, leaving business logic state strictly separated.

## Implementation Plan
The migration follows a strict strangler fig pattern, implemented over three specific cycles to ensure the stability of the 8-cycle workflow.

- **CYCLE01: E2B Sandbox Isolation**
  - **Focus:** Low Impact, High Yield. Migrate sandbox evaluation and QA nodes to the `@e2b/mcp-server`.
  - **Actions:** Update Dockerfile to include Node.js and `@e2b/mcp-server`. Implement the foundational `src/mcp_client_manager.py` targeting E2B. Refactor `sandbox_evaluator.py` and `qa.py` to bind E2B tools (`run_code`, `execute_command`). Deprecate legacy E2B services.

- **CYCLE02: GitHub Read-Only Operations**
  - **Focus:** Medium Impact. Migrate context gathering and repository reads to `@modelcontextprotocol/server-github`.
  - **Actions:** Add `@modelcontextprotocol/server-github` to the Docker environment. Extend `mcp_client_manager.py` to handle GitHub read connections. Refactor `architect.py`, `coder.py`, and `auditor.py` to use `get_file_content` natively. Remove prompt logic that manually asked the backend for file contents.

- **CYCLE03: GitHub Write Operations & Jules Orchestration**
  - **Focus:** High Risk. Complete the migration by moving write-enabled Git operations and parallel agent sessions to the MCP paradigm.
  - **Actions:** Add `@google/jules-mcp`. Refactor `master_integrator.py` to use GitHub write tools (`push_commit`, `create_pull_request`). Refactor `global_refactor.py` to orchestrate sessions via Jules MCP. Finally, delete the legacy `src/services/git/` and `src/services/jules/` directory trees entirely.

## Test Strategy

### CYCLE01
- **Unit Testing:** Create `tests/unit/test_mcp_client_manager.py` to ensure the `MultiMCPClient` connects successfully to standard I/O streams without real network calls. Test the `StdioServerParameters` with mocked environments.
- **Integration Testing:** Create `tests/ac_cdd/integration/test_mcp_node_integration.py` using dummy Node.js processes mimicking E2B schema.
- **Side-Effect Management:** Run executions purely on mock stdio pipes. The real E2B server will be isolated in the sandbox environments.

### CYCLE02
- **Unit Testing:** Verify tool schemas provided by the mock GitHub read-only server are accurately mapped to the LangGraph node states.
- **Integration Testing:** Implement `test_mcp_github_read_fallback()` to simulate `get_file_content` failure (file not found) and assert that `architect.py` gracefully requests alternative context.
- **Side-Effect Management:** Provide a local, temporary directory with dummy text files for the mock GitHub MCP to read, preventing it from touching the real repository.

### CYCLE03
- **Unit Testing:** Test mechanical gates ensuring write permissions are strictly limited to `master_integrator.py` and reject attempts from `auditor.py`.
- **Integration/E2E Testing:** Execute `test_mcp_jules_session_dispatch()` and `test_end_to_end_workflow.py` pointing the system to a dedicated, isolated test repository. Ensure PRs are successfully opened and sessions are managed cleanly.
- **Side-Effect Management:** Target an explicit, standalone GitHub repository created solely for automated testing. Validate that environment variables are strictly filtered (e.g., dropping `SUDO_*` commands) to prevent API key leakage into logs.