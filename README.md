# NITPICKERS: AI-Native Code Development Environment

An AI-native development environment based on a highly robust methodology designed to enforce absolute zero-trust validation of AI-generated code. NITPICKERS uses a 5-Phase Architecture, static analysis, dynamic testing in a secure sandbox, and automated red team auditing to ensure that generated code meets professional engineering standards.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Key Features

- **5-Phase Parallel & Sequential Architecture:** Seamlessly orchestrates requirement decomposition, parallel feature implementation, 3-Way Diff integration, and full-system E2E UI testing to manage scale and complexity.
- **Automated Mechanical Blockade (Zero-Trust Validation):** Pull requests are explicitly blocked until all static (Ruff, Mypy) and dynamic (Pytest) structural checks pass with a zero exit code.
- **Resilient 3-Way Diff Integration:** Ensures robust code integration from parallel coding cycles by combining standard Git merges with advanced LLM-based conflict resolution.
- **Multi-Modal Diagnostic Capture & Red Teaming:** Utilizes Vision LLMs (via OpenRouter) as stateless diagnostics to analyze E2E/Playwright test failure screenshots and provide structured remediation to coding agents.

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
        ArchSession["architect_session\n(Requirement Decomposition)"]
        ArchCritic{"self-critic review\n(Plan Review)"}
        InitCmd2 --> ArchSession
        ArchSession --> ArchCritic
        ArchCritic -- "Reject" --> ArchSession
    end

    %% Phase2: Coder Graph
    subgraph Phase2 ["Phase 2: Coder Graph (Parallel: Cycle 1...N)"]
        direction TB
        CoderSession["coder_session\n(Implementation & PR)"]
        SelfCritic["self_critic\n(Pre-Sandbox Polish)"]
        SandboxEval{"sandbox_evaluate\n(Linter / Unit Test)"}
        AuditorNode{"auditor_node\n(Serial: Auditor 1→2→3)"}
        RefactorNode["refactor_node\n(Apply Audit Feedback)"]
        FinalCritic{"final_critic\n(Self Final Review)"}

        CoderSession -- "First Pass" --> SelfCritic --> SandboxEval
        CoderSession -- "Subsequent" --> SandboxEval
        SandboxEval -- "Fail" --> CoderSession
        SandboxEval -- "Pass (Implementing)" --> AuditorNode
        SandboxEval -- "Pass (Refactoring)" --> FinalCritic
        AuditorNode -- "Reject" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode
        RefactorNode --> SandboxEval
        FinalCritic -- "Reject" --> CoderSession
    end

    %% Phase3: Integration Phase
    subgraph Phase3 ["Phase 3: Integration Phase"]
        direction TB
        MergeTry{"Local Git Merge\n(To Integration Branch)"}
        MasterIntegrator["master_integrator\n(3-Way Diff Resolution)"]
        GlobalSandbox{"global_sandbox\n(Global Linter/Pytest)"}
    end

    %% Phase4: UAT & QA Graph
    subgraph Phase4 ["Phase 4: UAT & QA Graph"]
        direction TB
        UatEval{"uat_evaluate\n(Playwright E2E Tests)"}
        QaAuditor["qa_auditor\n(Vision LLM Diagnostics)"]
        QaSession["qa_session\n(Apply Fixes)"]
        EndNode(((END)))
    end

    Phase0 --> Phase1
    Phase1 --> Phase2
    FinalCritic -- "Approve" --> MergeTry
    MergeTry -- "Conflict" --> MasterIntegrator
    MasterIntegrator --> MergeTry
    MergeTry -- "Success" --> GlobalSandbox
    GlobalSandbox -- "Fail" --> MasterIntegrator
    GlobalSandbox -- "Pass" --> UatEval
    UatEval -- "Fail" --> QaAuditor
    QaAuditor --> QaSession
    QaSession --> UatEval
    UatEval -- "Pass" --> EndNode
```

## Prerequisites

Ensure the following tools are available on your system:
- `uv` - Python package installer and resolver.
- `git` - Version control.
- `Docker` - (Optional but recommended).
- Valid API keys:
    - `JULES_API_KEY`
    - `E2B_API_KEY`
    - `OPENROUTER_API_KEY`

## Installation & Setup

We recommend utilizing Docker and our provided `setup.sh` script to quickly establish your environment as a "Sidecar" workflow.

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <your-repository>
   cd <your-repository>
   ```

2. Configure your core environment variables:
   ```bash
   cp .env.example .env
   # Add JULES_API_KEY, E2B_API_KEY, OPENROUTER_API_KEY
   ```

3. Setup Docker & CLI aliases (Optional but recommended):
   ```bash
   bash setup.sh
   source ~/.bashrc
   ```

## Usage

Use the CLI `nitpick` command to orchestrate the pipeline from your project directory.

### Quick Start
Initialize the project structure:
```bash
nitpick init
```
Generate specific implementation cycles based on your specs:
```bash
nitpick gen-cycles
```
Run the full 5-Phase orchestrated pipeline:
```bash
nitpick run-pipeline
```

## Development Workflow

We strictly adhere to typing and formatting standards enforced via `uv`:
```bash
# Run tests
uv run pytest

# Check code quality
uv run ruff check .
uv run mypy .
```

## Project Structure

```text
/
├── dev_documents/          # Specs, System Architecture, & Logs
├── src/                    # Main application code
│   ├── cli.py              # CLI Entrypoint
│   ├── graph.py            # LangGraph pipeline setups
│   ├── state.py            # Pydantic states (CycleState, IntegrationState)
│   ├── nodes/              # Execution logic mapping
│   └── services/           # Decoupled usecases & orchestration
├── tests/                  # Pytest unit & integration testing
├── tutorials/              # Marimo UAT Interactive Notebooks
├── pyproject.toml          # Tooling settings
└── README.md               # You are here
```

## License

MIT License
