# NITPICKERS

An AI-native development environment based on a highly robust methodology designed to enforce absolute zero-trust validation of AI-generated code. NITPICKERS uses static analysis, dynamic testing in a secure sandbox, and automated red team auditing to ensure that generated code meets professional engineering standards. This version introduces a powerful new 5-Phase Architecture, enabling parallel implementation, sequential auditing, and intelligent 3-Way diff conflict resolution.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Ruff](https://img.shields.io/badge/Ruff-Passed-success)
![Mypy](https://img.shields.io/badge/Mypy-Passed-success)
![Pytest](https://img.shields.io/badge/Pytest-Passed-success)

## Key Features

- **5-Phase Parallel & Sequential Architecture:** Seamlessly orchestrates requirement decomposition, parallel feature implementation, 3-Way Diff integration, and full-system E2E testing.
- **Serial Auditing and Refactoring Loops:** Code is strictly audited by multiple independent agents sequentially before entering a final refactoring loop, enforcing high standards of code quality.
- **Intelligent 3-Way Diff Conflict Resolution:** Merging concurrent modifications is handled securely and automatically via a dedicated Master Integrator that synthesizes conflicting changes by understanding the Base, Branch A, and Branch B code.
- **Automated Mechanical Blockade:** Zero-trust validation. Pull requests are explicitly blocked until all static (Ruff, Mypy) and dynamic (Pytest) structural checks pass with a zero exit code, eliminating assumed success.
- **Multi-Modal Diagnostic Capture:** Automatically capture rich UI failure context, including high-resolution screenshots and DOM traces, providing undeniable evidence of regressions.

## Architecture Overview

The system operates across 5 distinct phases to guarantee code quality from planning to final integration.

```mermaid
flowchart TD
    %% Phase0: Init Phase (CLI Setup)
    subgraph Phase0 ["Phase 0: Init Phase (CLI Setup)"]
        direction TB
        InitCmd([CLI: nitpick init])
        GenTemplates[".env.sample / .gitignore, strict ruff, mypy settings (Local)"]
        UpdateDocker["add .env path on docker-compose.yml (User)"]
        PrepareSpec["define ALL_SPEC.md (User)"]

        InitCmd --> GenTemplates --> UpdateDocker --> PrepareSpec
    end

    %% Phase1: Architect Graph
    subgraph Phase1 ["Phase 1: Architect Graph"]
        direction TB
        InitCmd2([CLI: nitpick gen-cycles])

        subgraph Architect_Phase ["JULES: Architect Phase"]
            ArchSession["architect_session\n(Requirement Decomposition)"]
            ArchCritic{"self-critic review\n(Plan Review)"}
        end

        OutputSpecs[/"Specs and UATs for each Cycle"/]

        PrepareSpec --> InitCmd2 --> ArchSession
        ArchSession --> ArchCritic
        ArchCritic -- "Reject" --> ArchSession
        ArchCritic -- "Approve" --> OutputSpecs
    end

    %% Phase2: Coder Graph
    subgraph Phase2 ["Phase 2: Coder Graph (Parallel: Cycle 1...N)"]
        direction TB
        CoderSession["JULES: coder_session\n(Implementation)"]
        SelfCritic["JULES: SelfCriticReview\n(Initial Review)"]
        SandboxEval{"LOCAL: sandbox_evaluate\n(Linter / Unit Test)"}

        AuditorNode{"OpenRouter: auditor_node\n(Serial: Auditor 1→2→3)"}
        RefactorNode["JULES: refactor_node\n(Refactoring)"]
        FinalCritic{"JULES: Final Self-critic\n(Final Review)"}

        OutputSpecs -->|Start Cycle N| CoderSession

        CoderSession -- "1st Time" --> SelfCritic --> SandboxEval
        CoderSession -- "2nd+ Time" --> SandboxEval

        SandboxEval -- "Fail" --> CoderSession
        SandboxEval -- "Pass (Implementing)" --> AuditorNode
        SandboxEval -- "Pass (Refactored)" --> FinalCritic

        AuditorNode -- "Reject" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode

        RefactorNode --> SandboxEval

        FinalCritic -- "Reject" --> CoderSession
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
        QaAuditor["OpenRouter: qa_auditor\n(Diagnostic Analysis)"]
        QaSession["JULES: qa_session\n(Integration Fixes)"]
        EndNode(((END: Project Complete)))
    end

    %% Inter-Phase Connections
    FinalCritic -- "Approve (All PRs Ready)" --> MergeTry

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

## Installation & Setup

The recommended way to use NITPICKERS is by cloning the repository and setting up the dependencies via `uv`.

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <your-repository>
   cd <your-repository>
   ```

2. Setup dependencies:
   ```bash
   uv sync
   ```

3. Configure your core environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and populate your JULES_API_KEY, E2B_API_KEY, and OPENROUTER_API_KEY.
   ```

## Usage

### Initialize Project Requirements

For new or external projects, running `nitpick init` is the mandatory first step. It automatically scaffolds the required directory structure (`src/`, `tests/`, `dev_documents/`), initializes Git, and configures your environment.

```bash
nitpick init
```
After initialization, follow the CLI prompts to fill in `ALL_SPEC.md` and `USER_TEST_SCENARIO.md` inside the `dev_documents/` folder before running generation commands.

### Generate Development Cycles (Phase 1)
Parse your raw architectural documents into structured specifications and UAT plans.
```bash
nitpick gen-cycles
```

### Run Full Orchestrated Pipeline (Phases 2, 3 & 4)
Execute the complete orchestrated 5-phase pipeline against your currently active project directory, automatically managing parallel implementation and final integration.
```bash
nitpick run-pipeline
```

### Interactive Tutorials (UAT Verification)
To experience the fully automated pipeline interactively, you can run our definitive Marimo tutorial locally.
```bash
uv run marimo edit tutorials/UAT_AND_TUTORIAL.py
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
