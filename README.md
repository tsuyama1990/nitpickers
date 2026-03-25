# NITPICKERS

An AI-native development environment based on a highly robust methodology designed to enforce absolute zero-trust validation of AI-generated code. NITPICKERS uses static analysis, dynamic testing in a secure sandbox, and automated red team auditing to ensure that generated code meets professional engineering standards.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Ruff](https://img.shields.io/badge/Ruff-Passed-success)
![Mypy](https://img.shields.io/badge/Mypy-Passed-success)
![Pytest](https://img.shields.io/badge/Pytest-Passed-success)

## Key Features

- **Automated Mechanical Blockade:** Zero-trust validation. Pull requests are explicitly blocked until all static (Ruff, Mypy) and dynamic (Pytest) structural checks pass with a zero exit code, eliminating assumed success.
- **5-Phase Parallel & Sequential Architecture:** Seamlessly orchestrates requirement decomposition, parallel feature implementation, 3-Way Diff integration, and full-system E2E UI testing.
- **Multi-Modal Diagnostic Capture:** Automatically capture rich UI failure context, including high-resolution screenshots and DOM traces via Playwright, providing undeniable evidence of frontend regressions.
- **Self-Healing Loop with Stateless Auditor:** Utilize advanced Vision LLMs (via OpenRouter) strictly as outer-loop diagnosticians. They analyze error artifacts without project context fatigue and return structured JSON fix plans to the Worker agent.
- **Total Observability:** Fully integrated LangSmith tracing visualizes complex LangGraph node transitions, internal state mutations, and multi-modal API payloads.

## Architecture Overview

The system operates across 5 distinct phases to guarantee code quality from planning to final integration.

```mermaid
flowchart TD
    %% Phase0: Init Phase (CLI Setup)
    subgraph Phase0 ["Phase 0: Init Phase (CLI Setup)"]
        direction TB
        InitCmd([CLI: nitpick init])
    end

    %% Phase1: Architect Graph
    subgraph Phase1 ["Phase 1: Architect Graph"]
        direction TB
        InitCmd2([CLI: nitpick gen-cycles])
        ArchSession["JULES: architect_session\n(Requirement Decomposition)"]
        InitCmd2 --> ArchSession
    end

    %% Phase2: Coder Graph
    subgraph Phase2 ["Phase 2: Coder Graph (Parallel: Cycle 1...N)"]
        direction TB
        CoderSession["JULES: coder_session\n(Implementation)"]
        SandboxEval{"LOCAL: sandbox_evaluate\n(Linter / Unit Test)"}
        AuditorNode{"OpenRouter: auditor_node\n(Serial: Auditor 1→2→3)"}
        RefactorNode["JULES: refactor_node\n(Refactoring)"]

        CoderSession --> SandboxEval
        SandboxEval -- "Pass" --> AuditorNode
        AuditorNode -- "Reject" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode
        RefactorNode --> SandboxEval
    end

    %% Phase3: Integration Phase
    subgraph Phase3 ["Phase 3: Integration Phase"]
        direction TB
        MergeTry{"Local: Git PR Merge\n(Integration Branch)"}
        MasterIntegrator["JULES: master_integrator\n(3-Way Diff Resolution)"]
        GlobalSandbox{"LOCAL: global_sandbox\n(Global Linter/Pytest)"}
    end

    %% Phase4: UAT & QA Graph
    subgraph Phase4 ["Phase 4: UAT & QA Graph"]
        direction TB
        UatEval{"LOCAL: uat_evaluate\n(Playwright E2E Tests)"}
        UxAuditor["OpenRouter: ux_auditor\n(Multimodal UX Review)"]
        QaAuditor["OpenRouter: qa_auditor\n(Diagnostic Analysis)"]
        QaSession["JULES: qa_session\n(Integration Fixes)"]
    end

    %% Inter-Phase Connections
    Phase0 --> Phase1
    Phase1 --> Phase2
    Phase2 -- "All Coder Cycles Complete" --> MergeTry

    MergeTry -- "Conflict" --> MasterIntegrator
    MasterIntegrator --> MergeTry
    MergeTry -- "Success" --> GlobalSandbox

    GlobalSandbox -- "Pass" --> UatEval

    UatEval -- "Fail" --> QaAuditor
    UatEval -- "Pass" --> UxAuditor
    QaAuditor --> QaSession
    QaSession --> UatEval
```

## Prerequisites

Ensure the following tools are available on your system:
- `uv` - The fastest Python package installer and resolver.
- `git` - Version control for your codebase.
- `Docker` - (Optional, depending on sandbox configuration).
- Valid API keys:
    - `JULES_API_KEY` (Gemini Pro/Worker)
    - `E2B_API_KEY` (Sandbox Execution)
    - `OPENROUTER_API_KEY` (Auditor/Vision Models)
- LangSmith Observability Configuration (Optional):
    - `LANGCHAIN_TRACING_V2=true`
    - `LANGCHAIN_API_KEY`
    - `LANGCHAIN_PROJECT`

## Installation & Setup (Docker Recommended)

The primary and recommended way to use NITPICKERS is via Docker. This ensures a clean, isolated environment and simplifies dependency management. It operates efficiently in a "Sidecar" workflow, meaning you can mount any target project directory directly into the tool's container to seamlessly audit, build, and interact with external codebases.

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <your-repository>
   cd <your-repository>
   ```

2. Configure your core environment variables (Tool-Level):
   ```bash
   cp .env.example .env
   # Edit .env and populate your JULES_API_KEY, E2B_API_KEY, OPENROUTER_API_KEY, and (optionally) LangSmith variables.
   # These tool-level infrastructure keys should stay within the nitpickers directory.
   ```

3. Quick Start (Build & Alias):
   ```bash
   bash setup.sh
   ```
   The `setup.sh` script will automatically build the container and optionally add a `nitpick` alias to your `~/.bashrc`. This allows you to run `nitpick` commands from anywhere.

## Usage

Once your core `.env` is configured and you have run the setup script, you can navigate to *any* project directory and use the `nitpick` command seamlessly. Project-specific API keys should be placed in a separate `.env` file within the target project directory.

The "Sidecar" workflow dynamically mounts your current working directory into the container using the `TARGET_PROJECT_PATH` alias configuration.

### Initialize Project Requirements

For new or external projects, place your initial requirement documents (e.g., `ALL_SPEC.md`) inside the target project's `dev_documents/` folder *before* running generation commands.

```bash
mkdir -p /path/to/target/project/dev_documents/
# Place ALL_SPEC.md in the directory above
```

### Generate Development Cycles (Phase 1)
Navigate to your target project and parse your raw architectural documents into structured specifications and UAT plans.
```bash
cd /path/to/target/project
nitpick gen-cycles
```

### Run Full Orchestrated Pipeline (Phase 2, 3 & 4)
Execute the complete orchestrated 5-phase pipeline against your currently active project directory, automatically managing parallel implementation and final integration.
```bash
nitpick run-pipeline
```

### Run a Specific Cycle Manually
For debugging, execute a specific development cycle (e.g., `01`).
```bash
nitpick run-cycle --id 01
```

### Interactive Tutorials (UAT Verification)
To experience the fully automated, multi-modal User Acceptance Testing (UAT) pipeline interactively, you can run our definitive Marimo tutorial locally (requires local `uv` installation).
```bash
uv run marimo edit tutorials/nitpickers_5_phase_architecture.py
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
│   ├── system_prompts/     # Cycle specific plans and documents
│   └── USER_TEST_SCENARIO.md
├── src/                    # The main implementation for NITPICKERS
│   ├── cli.py              # CLI entrypoint
│   ├── state.py            # Pydantic state models (CycleState, etc.)
│   ├── graph.py            # Main LangGraph declarations
│   ├── nodes/              # LangGraph node routing functions
│   └── services/           # Orchestration (workflow.py) & Diff Logic (conflict_manager.py)
├── tests/                  # Unit, Integration, and UAT tests
├── tutorials/              # Marimo-based interactive tutorials
├── pyproject.toml          # Project configuration (Dependencies & Linting)
└── README.md               # User documentation
```

## License

MIT License
