# NITPICKERS

An AI-native development environment based on a highly robust methodology designed to enforce absolute zero-trust validation of AI-generated code. NITPICKERS uses static analysis, dynamic testing in a secure sandbox, and automated red team auditing to ensure that generated code meets professional engineering standards.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Ruff](https://img.shields.io/badge/Ruff-Passed-success)
![Mypy](https://img.shields.io/badge/Mypy-Passed-success)
![Pytest](https://img.shields.io/badge/Pytest-Passed-success)

## Key Features

- **Automated Mechanical Blockade:** Zero-trust validation. Pull requests are explicitly blocked until all static (Ruff, Mypy) and dynamic (Pytest) structural checks pass with a zero exit code.
- **5-Phase Parallel & Sequential Architecture:** Seamlessly orchestrates requirement decomposition, parallel feature implementation, 3-Way Diff integration, and full-system E2E UI testing.
- **Self-Healing Loop with Stateless Auditor:** Utilize advanced Vision LLMs strictly as outer-loop diagnosticians. They analyze error artifacts without project context fatigue and return structured JSON fix plans.
- **Intelligent 3-Way Diff Resolution:** Resolves complex Git merge conflicts dynamically by structurally comparing the Base, Branch A, and Branch B code states instead of raw conflict markers.
- **Multi-Modal Diagnostic Capture:** Automatically capture rich UI failure context, including high-resolution screenshots and DOM traces via Playwright for undeniable evidence of frontend regressions.

## Architecture Overview

The system operates across 5 distinct phases to guarantee code quality from planning to final integration.

```mermaid
flowchart TD
    %% Phase 0: Init Phase (CLI Setup)
    subgraph Phase0 ["Phase 0: Init Phase (CLI Setup)"]
        direction TB
        InitCmd([CLI: nitpick init])
    end

    %% Phase 1: Architect Graph
    subgraph Phase1 ["Phase 1: Architect Graph"]
        direction TB
        InitCmd2([CLI: nitpick gen-cycles])
        ArchSession["JULES: architect_session"]
        ArchCritic{"JULES: architect_critic"}
        InitCmd2 --> ArchSession
        ArchSession --> ArchCritic
        ArchCritic -- "Reject" --> ArchSession
    end

    %% Phase 2: Coder Graph (Parallel: Cycle 1...N)
    subgraph Phase2 ["Phase 2: Coder Graph (Parallel)"]
        direction TB
        CoderSession["JULES: coder_session"]
        SelfCritic["JULES: self_critic"]
        SandboxEval{"LOCAL: sandbox_evaluate"}
        AuditorNode{"OpenRouter: auditor_node (Serial)"}
        RefactorNode["JULES: refactor_node"]
        FinalCritic{"JULES: final_critic"}

        CoderSession --> SelfCritic
        SelfCritic --> SandboxEval
        SandboxEval -- "Pass" --> AuditorNode
        AuditorNode -- "Reject" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode
        RefactorNode --> SandboxEval
        SandboxEval -- "Pass (Post-Refactor)" --> FinalCritic
        FinalCritic -- "Reject" --> CoderSession
    end

    %% Phase 3: Integration Phase
    subgraph Phase3 ["Phase 3: Integration Phase"]
        direction TB
        MergeTry{"Local: Git PR Merge"}
        MasterIntegrator["JULES: master_integrator (3-Way Diff)"]
        GlobalSandbox{"LOCAL: global_sandbox"}
    end

    %% Phase 4: UAT & QA Graph
    subgraph Phase4 ["Phase 4: UAT & QA Graph"]
        direction TB
        UatEval{"LOCAL: uat_evaluate"}
        QaAuditor["OpenRouter: qa_auditor"]
        QaSession["JULES: qa_session"]
    end

    Phase0 --> Phase1
    Phase1 --> Phase2
    Phase2 -- "All Cycles Complete" --> MergeTry
    MergeTry -- "Conflict" --> MasterIntegrator
    MasterIntegrator --> MergeTry
    MergeTry -- "Success" --> GlobalSandbox
    GlobalSandbox -- "Pass" --> UatEval
    UatEval -- "Fail" --> QaAuditor
    QaAuditor --> QaSession
    QaSession --> UatEval
```

## Prerequisites

Ensure the following tools are available on your system:
- `Python 3.12+`
- `uv` - The fastest Python package installer and resolver.
- `git` - Version control for your codebase.
- `Docker` - (Optional, depending on sandbox configuration).
- Valid API keys:
    - `JULES_API_KEY` (Gemini Pro/Worker)
    - `E2B_API_KEY` (Sandbox Execution)
    - `OPENROUTER_API_KEY` (Auditor/Vision Models)

## Installation & Setup

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <your-repository>
   cd <your-repository>
   ```

2. Sync the dependencies utilizing `uv`:
   ```bash
   uv sync
   ```

3. Configure your core environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and populate your JULES_API_KEY, E2B_API_KEY, and OPENROUTER_API_KEY.
   ```

4. Quick Start (Docker Alias - Recommended):
   ```bash
   bash setup.sh
   source ~/.bashrc
   ```

## Usage

Once configured, you can use the `nitpick` command seamlessly to execute the pipeline.

### Initialize Project Requirements
For new or external projects, running `nitpick init` is the mandatory first step. It automatically scaffolds the required directory structure (`src/`, `tests/`, `dev_documents/`), initializes Git, and configures your environment.

```bash
nitpick init
```
After initialization, ensure `dev_documents/ALL_SPEC.md` and `dev_documents/USER_TEST_SCENARIO.md` are correctly filled before generating cycles.

### Generate Development Cycles (Phase 1)
Parse your raw architectural documents into structured specifications for Phase 2 implementation.
```bash
nitpick gen-cycles
```

### Run Full Orchestrated Pipeline (Phase 2, 3 & 4)
Execute the complete orchestrated 5-phase pipeline, handling parallel cycle implementation, 3-Way Diff integration, and UI acceptance tests.
```bash
nitpick run-pipeline
```

### Interactive Tutorials (UAT Verification)
To experience the fully automated multi-modal UAT pipeline interactively via Marimo (our definitive CI test):
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
│   ├── system_prompts/     # Cycle specific architecture & UAT docs
│   └── USER_TEST_SCENARIO.md
├── src/                    # The main implementation for NITPICKERS
│   ├── cli.py              # CLI entrypoint
│   ├── state.py            # Phase 2 Routing Extensions (CycleState)
│   ├── graph.py            # LangGraph routing construction
│   ├── nodes/              # Routers and Node logic
│   ├── domain_models/      # Strict Pydantic Contracts (e.g. ConflictPackage)
│   └── services/           # Orchestration (workflow.py) & Diff Logic (conflict_manager.py)
├── tests/                  # Unit, Integration, and UAT tests
├── pyproject.toml          # Project configuration (Dependencies & Linting)
└── README.md               # User documentation
```

## License

MIT License
