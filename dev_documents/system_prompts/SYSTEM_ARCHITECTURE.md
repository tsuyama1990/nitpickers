# System Architecture

## Summary
The Nitpickers platform is transitioning from a legacy "API Wrapper" architecture to a modern "MCP Router" paradigm. Historically, the Python backend manually wrapped external API calls (e.g., GitHub, E2B, Jules), creating brittle interdependencies and requiring continuous manual updates to prompt schemas and response parsers. The new architecture integrates the Model Context Protocol (MCP) using standalone Node.js sidecar servers. This allows Large Language Model (LLM) agents to natively invoke standardized tools via JSON-RPC 2.0. By decoupling the LLM from underlying API mechanics, the core Python application focuses entirely on multi-agent orchestration, state management, and LangGraph logic.

## System Design Objectives
The primary objectives of this architectural shift are to reduce maintenance overhead, eliminate technical debt, and significantly improve the robustness of the 8-cycle multi-agent workflow.

1. **Decoupling and Standardization:** Transition the application from a rigid API Wrapper to an MCP Router. This offloads tool execution, payload formatting, authentication, and error handling to standardized, vendor-maintained MCP servers (GitHub, E2B, Jules).
2. **Native LLM Tool Calling:** Leverage the built-in function-calling capabilities of modern LLMs. MCP servers will advertise their available tools, semantic descriptions, and strongly-typed required schemas directly to the LLM upon initialization.
3. **Resilience and Determinism:** Eliminate the fragility associated with custom parsers breaking on edge-case API responses (e.g., Git merge conflicts, E2B timeout stack traces). The MCP servers will execute operations securely and return natively formatted context payloads back to the LLMs.
4. **Seamless Integration:** The architectural transition must strictly preserve the existing 8-cycle workflow from the user's perspective. No changes will be made to the fundamental user experience, state persistence (e.g., `project_state.json`), or out-of-scope external tools (like web search).
5. **Secure Execution:** API keys and sensitive environment variables will be securely managed and routed only to the specific MCP subprocesses that require them, reducing authentication sprawl across the Python codebase. A strict sanitization layer must strip injected variables (like `SUDO_COMMAND`) to prevent leakage during subprocess boot.

## System Architecture
The new system architecture introduces three standalone Node.js MCP Server sidecars (`@modelcontextprotocol/server-github`, `@e2b/mcp-server`, `@google/jules-mcp`) communicating with the main Python application via the `stdio` transport layer.

- **MCP Router Module (`src/mcp_router/`):** A modular package responsible for the lifecycle of the MCP subprocesses. It uses `pydantic-settings` to securely load credentials, manages concurrent connection pooling via `asynccontextmanager` to prevent zombie Node processes, and exposes cleanly filtered toolsets via Dependency Injection to dynamic agent nodes.
- **LangGraph Agents:** The existing LangGraph nodes (e.g., Coder, Auditor, Master Integrator, Sandbox Evaluator) will be heavily refactored. They will dynamically bind to the isolated tool arrays injected by the workflow builder (`src/cli.py` or `src/workflow/`).
- **Explicit Boundary Management (Mechanical Gates):** Write tools (e.g., `push_commit`, `create_pull_request`) are strictly constrained to write-enabled nodes like the Master Integrator. Read-only nodes (e.g., Architect) will only receive read-only tools, physically preventing hallucinated destructive actions.

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
        subgraph MCP_Router [src/mcp_router/]
            Config[Pydantic Settings]
            Manager[Lifecycle Manager]
            Tools[Tool Filtering]
            Config --> Manager --> Tools
        end

        Manager -->|stdio| G_MCP
        Manager -->|stdio| E_MCP
        Manager -->|stdio| J_MCP

        subgraph Agents [LangGraph Nodes]
            C[Coder Agent]
            A[Auditor Agent]
            MI[Master Integrator]
            SE[Sandbox Evaluator]
        end

        Tools -->|Injects filtered toolsets| Agents
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
    TR -.-> Manager
```

## Design Architecture
The file structure and component design reflect the transition from custom services to standard, robust MCP integrations utilizing explicit modularity.

```text
/
├── dev_documents/
│   ├── ALL_SPEC.md
│   ├── USER_TEST_SCENARIO.md
│   ├── ARCHITECT_CRITIC_REVIEW.md
│   └── system_prompts/
│       ├── SYSTEM_ARCHITECTURE.md
│       ├── CYCLE01/
│       ├── CYCLE02/
│       └── CYCLE03/
├── src/
│   ├── cli.py                 (REFACTORED: Initializes MCP context and injects tools into graph)
│   ├── mcp_router/            (NEW MODULE: Replaces legacy monolithic managers)
│   │   ├── __init__.py
│   │   ├── schemas.py         (NEW: Pydantic Settings for API validation)
│   │   ├── manager.py         (NEW: Async Context Manager for subprocesses)
│   │   └── tools.py           (NEW: Mechanical gate tool filtering)
│   ├── domain_models/
│   │   └── project_state.py   (EXISTING: Kept as-is for state persistence)
│   ├── nodes/
│   │   ├── architect.py       (REFACTORED: Receives injected read-only GitHub MCP tools)
│   │   ├── auditor.py         (REFACTORED: Receives injected read-only tools)
│   │   ├── coder.py           (REFACTORED: Receives injected E2B and GitHub read tools)
│   │   ├── master_integrator.py (REFACTORED: Receives injected GitHub write MCP tools)
│   │   └── sandbox_evaluator.py (REFACTORED: Receives strictly injected E2B MCP tools)
│   └── templates/             (REFACTORED: System prompts updated to utilize native tool calling)
├── tests/
│   ├── unit/
│   │   └── test_mcp_router.py
│   └── ac_cdd/
│       └── integration/
│           ├── test_mcp_node_integration.py
│           └── test_end_to_end_workflow.py
├── pyproject.toml             (MODIFIED: Adds pydantic-settings, mcp, langchain-mcp-adapters)
├── Dockerfile                 (REFACTORED: Adds Node.js runtime and global MCP servers)
└── docker-compose.yml
```

### Core Domain Pydantic Models Structure and Typing
The configuration module `src/mcp_router/schemas.py` utilizes `pydantic-settings` to robustly parse the `.env` file and validate state before subprocess execution.
- `E2BMcpConfig`, `GitHubMcpConfig`, `JulesMcpConfig`: Subclasses of `BaseSettings` ensuring environment variables (e.g., `GITHUB_PERSONAL_ACCESS_TOKEN`, `E2B_API_KEY`) are present, failing immediately on application boot if they are missing or blank.
- The existing objects like `CycleState` and `ProjectManifest` remain untouched, ensuring the state tracker does not require an overhaul. The new models integrate purely to configure the MCP environment, separating configuration concerns from business logic state.

## Implementation Plan
The migration follows a strict strangler fig pattern, implemented over three specific cycles to ensure the stability of the 8-cycle workflow.

- **CYCLE01: E2B Sandbox Isolation**
  - **Focus:** Low Impact, High Yield. Migrate sandbox evaluation and QA nodes to the `@e2b/mcp-server`.
  - **Actions:** Update Dockerfile to include Node.js and `@e2b/mcp-server`. Implement the foundational `src/mcp_router/` module targeting E2B. Implement strict subprocess lifecycle using `asynccontextmanager`. Refactor `sandbox_evaluator.py` and `qa.py` to accept injected E2B tools (`run_code`, `execute_command`). Deprecate legacy E2B services.

- **CYCLE02: GitHub Read-Only Operations**
  - **Focus:** Medium Impact. Migrate context gathering and repository reads to `@modelcontextprotocol/server-github`.
  - **Actions:** Add `@modelcontextprotocol/server-github` to the Docker environment. Extend `schemas.py` and `manager.py` to handle GitHub read connections. Implement `tools.py` filtering logic. Refactor `architect.py`, `coder.py`, and `auditor.py` to natively use `get_file_content` via Dependency Injection. Remove prompt logic that manually asked the backend for file contents.

- **CYCLE03: GitHub Write Operations & Jules Orchestration**
  - **Focus:** High Risk. Complete the migration by moving write-enabled Git operations and parallel agent sessions to the MCP paradigm.
  - **Actions:** Add `@google/jules-mcp`. Extend `schemas.py`. Refactor `tools.py` to isolate `push_commit` and `create_pull_request` strictly for `master_integrator.py`. Refactor `global_refactor.py` to orchestrate sessions via Jules MCP. Finally, delete the legacy `src/services/git/` and `src/services/jules/` directory trees entirely.

## Test Strategy

### CYCLE01
- **Unit Testing:** Create `tests/unit/test_mcp_router.py` to ensure `McpClientManager` sanitizes `os.environ` properly (dropping `SUDO_*` variables), correctly tears down subprocesses upon context exit, and correctly parses `pydantic-settings`.
- **Integration Testing:** Create `tests/ac_cdd/integration/test_mcp_node_integration.py` using dummy Node.js processes mimicking the E2B schema.
- **Side-Effect Management:** Run executions purely on mock stdio pipes. The real E2B server will be isolated in real sandbox environments during UAT.

### CYCLE02
- **Unit Testing:** Verify `tools.py` successfully filters the GitHub read-only toolset to ensure `push_commit` is absent.
- **Integration Testing:** Implement `test_mcp_github_read_fallback()` simulating `get_file_content` failure (404) and asserting that `architect.py` gracefully recovers.
- **Side-Effect Management:** Provide a local, temporary directory with dummy text files for the mock GitHub MCP to read, preventing it from touching the real repository.

### CYCLE03
- **Unit Testing:** Test mechanical gates ensuring write tools are successfully injected only into `master_integrator.py`.
- **Integration/E2E Testing:** Execute `test_mcp_jules_session_dispatch()` and `test_end_to_end_workflow.py` pointing the system to an isolated test repository. Ensure PRs are successfully opened and sessions are managed cleanly.
- **Side-Effect Management:** Target an explicit, standalone GitHub repository created solely for automated testing. Validation of telemetry parsing across the graph bounds.