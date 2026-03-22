# Nitpickers: MCP-Routed Code Development Environment

An AI-native development environment based on a highly robust methodology designed to enforce absolute zero-trust validation of AI-generated code. Nitpickers uses static analysis, dynamic testing in a secure sandbox, and automated red team auditing to ensure that generated code meets professional engineering standards. This next-generation version is entirely powered by the **Model Context Protocol (MCP)**, allowing agents to natively and deterministically interact with external tools.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Key Features

- **MCP Router Paradigm:** Completely decoupled infrastructure using Node.js MCP Sidecars. The system inherently maps the latest GitHub, E2B, and Jules interactions directly to the LLM context window using standard JSON-RPC 2.0 tool binding, eliminating brittle legacy Python wrappers.
- **Automated Mechanical Blockade:** Zero-trust validation. Pull requests are explicitly blocked until all static (Ruff, Mypy) and dynamic (Pytest) structural checks pass with a zero exit code via the deterministic E2B MCP server.
- **Docs-as-Tests Integration:** Natively parse and execute `uat-scenario` blocks directly from markdown specifications (`ALL_SPEC.md`).
- **Parallel Fleet Orchestration:** Leveraging the Jules MCP, dispatch cloud worker agents safely and quickly to run repository-scale refactoring tasks with seamless telemetry integration.

## Architecture Overview

The Nitpickers pipeline utilizes an `MCP Client Manager` to bridge LangGraph-based workflow nodes directly to robust, vendor-maintained MCP sidecars via the `stdio` transport layer.

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

## Prerequisites

Ensure the following tools are available on your system:
- `uv` - The fastest Python package installer and resolver.
- `git` - Version control for your codebase.
- `Docker` - Including `Node.js` globally configured via the provided `Dockerfile`.
- Valid API keys:
    - `GITHUB_PERSONAL_ACCESS_TOKEN` (Read/Write Code)
    - `JULES_API_KEY` (Gemini Pro/Worker)
    - `E2B_API_KEY` (Sandbox Execution)
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

2. Sync the dependencies and initialize the virtual environment:
   ```bash
   uv sync
   ```

3. Configure your environment variables. Ensure the `SUDO_COMMAND` or similar injected keys are strictly mapped:
   ```bash
   cp .env.example .env
   # Edit .env and populate your API keys and LangSmith variables.
   ```

## Usage

Nitpickers operates primarily through its Command-Line Interface, navigating the development cycles defined by the system architecture.

### Interactive Tutorials (UAT Verification)
To experience the new architecture pipelines interactively, run the definitive Marimo tutorial. It supports both **Mock Mode** (no API keys required) and **Real Mode**.
```bash
uv run marimo run tutorials/automated_uat_pipeline_tutorial.py
```

### Generate Development Cycles (Phase 1)
Parse your raw architectural documents into structured specifications and UAT plans.
```bash
uv run python -m src.cli gen-cycles
```

### Run a Specific Cycle (Phase 2 & 3)
Execute a specific development cycle (e.g., `01`) defined by the manifest. The system will map standard MCP tools dynamically and evaluate the E2B code executions.
```bash
uv run python -m src.cli run-cycle --id 01
```

## Development Workflow

-   **Run Linters & Type Checks:**
    ```bash
    uv run ruff check .
    uv run mypy .
    ```
-   **Run Unit & Integration Tests:**
    ```bash
    uv run pytest
    ```

## Project Structure

```text
/
├── dev_documents/          # Auto-generated specs, UATs, logs
├── src/                    # The main implementation for NITPICKERS
│   ├── cli.py              # CLI entrypoint
│   ├── mcp_client_manager.py # Manages lifecycle of MCP sidecars
│   ├── domain_models/      # Pydantic schemas enforcing interface locks
│   ├── nodes/              # LangGraph workflow nodes
│   └── templates/          # System prompts for the agents
├── tests/                  # Unit, Integration, and UAT tests
│   └── ac_cdd/             # Integration tests utilizing mock stdio pipes
├── tutorials/              # Marimo-based interactive tutorials
├── pyproject.toml          # Project configuration (Dependencies & Linting)
└── README.md               # User documentation
```

## License

MIT License
