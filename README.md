# NITPICKERS

An AI-native development environment based on a highly robust methodology designed to enforce absolute zero-trust validation of AI-generated code. NITPICKERS uses static analysis, dynamic testing in a secure sandbox, and automated red team auditing to ensure that generated code meets professional engineering standards.

**The core integration engine has been radically upgraded to an "MCP Router" architecture.** By leveraging the standardized Model Context Protocol (MCP), Nitpickers delegates complex, brittle API interactions (GitHub, E2B Sandboxes, Jules Agent Fleets) directly to specialized Node.js sidecars. This eliminates massive amounts of custom Python middleware, allowing the LangGraph orchestrator to focus purely on resilient state transitions and deterministic multi-agent logic natively via LLM tool calling.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Key Features

- **MCP Router Architecture:** Zero-trust external integrations. The system offloads API execution to `@modelcontextprotocol/server-github`, `@e2b/mcp-server`, and `@google/jules-mcp` via efficient Stdio transport, drastically reducing codebase maintenance and API wrapper fragility.
- **Native LLM Tool Calling:** Agents natively bind to standard JSON-RPC 2.0 tools instead of relying on heavily prompted Pydantic parsers, gracefully handling multi-line merge conflicts or complex cloud execution timeouts without crashing the graph state.
- **Mechanical Principle of Least Privilege:** Security is enforced at the graph level, not just via prompts. Read-only nodes (like the Architect) are structurally blocked from accessing mutating tools (like `push_commit`), ensuring deterministic and safe repository exploration.
- **Automated Mechanical Blockade:** Zero-trust validation. Pull requests are explicitly blocked until all static (Ruff, Mypy) and dynamic (Pytest) structural checks pass with a zero exit code, eliminating assumed success.
- **Docs-as-Tests Integration:** Natively parse and execute `uat-scenario` blocks directly from markdown specifications (`ALL_SPEC.md`), ensuring the implementation accurately reflects the documented requirements.
- **Multi-Modal Diagnostic Capture:** Automatically capture rich UI failure context, including high-resolution screenshots and DOM traces via Playwright, providing undeniable evidence of frontend regressions.
- **Total Observability:** Fully integrated LangSmith tracing visualizes complex LangGraph node transitions, internal state mutations, and multi-modal API payloads, transforming the "Black Box" of agent execution into quantifiable, debuggable datasets.

## Architecture Overview

The NITPICKERS pipeline is designed around a strictly decoupled Worker-Auditor-Observer paradigm, now powered by a central `McpClientManager`.

-   **Stateful Worker (Inner Loop):** Generates code and tests, maintaining project context across iterations.
-   **MCP Router (Integration Layer):** Dynamically binds standard tools from Node.js sidecars to the LLM context, handling the execution of all external operations (Git, Sandboxing, Fleet Dispatch) natively.
-   **Sandbox (Gatekeeper):** A secure execution environment using `ProcessRunner` that mechanically halts the pipeline on any failure, generating multi-modal artifacts when UI tests break.
-   **Stateless Auditor (Outer Loop):** Diagnoses isolated failures using Vision LLMs and returns precise JSON fix plans to the Worker.
-   **Observability Layer:** LangSmith silently traces all graph transitions and state mutations to prevent infinite loops and hallucinated logic.

```mermaid
graph TD
    subgraph Core System [Python LangGraph Application]
        direction TB
        SM[State Manager]
        CM[MCP Client Manager]
        N_Arch[Architect Node]
        N_Code[Coder Node]

        N_Arch --> CM
        N_Code --> CM
        SM -.-> N_Arch
    end

    subgraph MCP Servers [Node.js Sidecars via Stdio]
        MCP_GH[@modelcontextprotocol/server-github]
        MCP_E2B[@e2b/mcp-server]
    end

    CM <-->|JSON-RPC via Stdio| MCP_GH
    CM <-->|JSON-RPC via Stdio| MCP_E2B
```

## Prerequisites

Ensure the following tools are available on your system:
- `uv` - The fastest Python package installer and resolver.
- `Node.js` (v18+) - Required for running the MCP sidecar servers.
- `git` - Version control for your codebase.
- Valid API keys:
    - `GITHUB_PERSONAL_ACCESS_TOKEN` (Repository Interactions)
    - `E2B_API_KEY` (Sandbox Execution)
    - `JULES_API_KEY` (Agent Fleet Orchestration)
    - `OPENROUTER_API_KEY` (Auditor/Vision Models)
- LangSmith Observability Configuration:
    - `LANGCHAIN_TRACING_V2=true`
    - `LANGCHAIN_API_KEY`
    - `LANGCHAIN_PROJECT`

## Installation & Setup

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <your-repository>
   cd <your-repository>
   ```

2. Globally install the required MCP server sidecars to ensure rapid boot times:
   ```bash
   npm install -g @modelcontextprotocol/server-github @e2b/mcp-server @google/jules-mcp
   ```

3. Sync the dependencies and initialize the virtual environment:
   ```bash
   uv sync
   ```

4. Configure your environment variables. The Gatekeeper explicitly requires LangSmith to be configured before any execution will start:
   ```bash
   cp .env.example .env
   # Edit .env and populate your API keys and LangSmith variables.
   ```

## Usage

NITPICKERS operates primarily through its Command-Line Interface.

### Interactive Tutorials (UAT Verification)
To experience the new MCP Router architecture and multi-modal testing pipeline interactively, run the definitive Marimo tutorial. It natively supports both **Mock Mode** (no API keys required) and **Real Mode**.
```bash
uv run marimo edit tutorials/mcp_router_architecture_validation.py
```

### Generate Development Cycles (Phase 1)
Parse your raw architectural documents into structured specifications and UAT plans.
```bash
uv run python -m src.cli gen-cycles
```

### Run a Specific Cycle (Phase 2 & 3)
Execute a specific development cycle (e.g., `01`) defined by the manifest. The system will automatically utilize the MCP sidecars to interact securely with GitHub and the E2B sandbox.
```bash
uv run python -m src.cli run-cycle --id 01
```

### Finalize & Refactor
```bash
uv run python -m src.cli finalize-session
```

## Troubleshooting

- **Hard Stop during execution:** If the execution halts with an "Environment & Observability Verification" error, ensure your `.env` is correctly populated with `LANGCHAIN_TRACING_V2=true` and valid LangSmith keys.
- **MCP Server Boot Failure:** Ensure `Node.js` is correctly installed in your path and the `@modelcontextprotocol/server-github` packages have been installed globally via `npm`.

## Development Workflow

The migration to the MCP Router architecture is divided into three strict development cycles (`CYCLE01` - `CYCLE03`). When contributing, ensure your changes adhere to the cycle specifications located in `dev_documents/system_prompts/`.

-   **Run Linters & Type Checks:**
    ```bash
    uv run ruff check .
    uv run mypy .
    ```
-   **Run Unit & Integration Tests:**
    ```bash
    uv run pytest
    ```
-   **Run UATs manually:**
    ```bash
    uv run pytest tests/uat/ --browser=chromium
    ```

## Project Structure

```text
/
├── dev_documents/          # Auto-generated specs, UATs, logs
├── src/                    # The main implementation for NITPICKERS
│   ├── cli.py              # CLI entrypoint
│   ├── domain_models/      # Pydantic schemas enforcing interface locks
│   ├── nodes/              # LangGraph workflow nodes
│   ├── services/           # MCP Client Manager and business logic
│   └── templates/          # System prompts for the agents
├── tests/                  # Unit, Integration, and UAT tests
│   └── uat/                # Dynamic UAT scripts (Marimo/Pytest)
├── tutorials/              # Marimo-based interactive tutorials
├── pyproject.toml          # Project configuration (Dependencies & Linting)
└── README.md               # User documentation
```

## License

MIT License
