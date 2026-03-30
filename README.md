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
    subgraph Phase0 ["Phase 0: Init Phase (CLI Setup)"]
        direction TB
        InitCmd([CLI: nitpick init])
    end

    subgraph Phase1 ["Phase 1: Architect Graph"]
        direction TB
        InitCmd2([CLI: nitpick gen-cycles])
        ArchSession["JULES: architect_session\n(Requirement Decomposition)"]
        ArchCritic{"JULES: architect_critic\n(Red Team Self-Critic)"}
        InitCmd2 --> ArchSession
        ArchSession --> ArchCritic
        ArchCritic -- "Reject" --> ArchSession
    end

    subgraph Phase2 ["Phase 2: Coder Graph (Parallel: Cycle 1...N)"]
        direction TB
        CoderSession["JULES: coder_session\n(Test/Implementation)"]
        SelfCritic["JULES: self_critic\n(Pre-Sandbox Polish)"]
        SandboxEval{"LOCAL: sandbox_evaluate\n(Linter / Unit Test)"}
        AuditorNode{"OpenRouter: auditor_node\n(Serial: Auditor 1→2→3)"}
        RefactorNode["JULES: refactor_node\n(Post-Audit Refactor)"]
        FinalCritic["JULES: final_critic\n(Final Logic Verification)"]

        CoderSession --> SelfCritic
        SelfCritic --> SandboxEval
        SandboxEval -- "Fail" --> CoderSession
        SandboxEval -- "Pass (Not Refactoring)" --> AuditorNode
        AuditorNode -- "Reject" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode
        RefactorNode --> SandboxEval
        SandboxEval -- "Pass (Refactoring)" --> FinalCritic
        FinalCritic -- "Reject" --> CoderSession
    end

    subgraph Phase3 ["Phase 3: Integration Phase"]
        direction TB
        MergeTry{"Local: Git PR Merge\n(Integration Branch)"}
        MasterIntegrator["JULES: master_integrator\n(3-Way Diff Resolution)"]
        GlobalSandbox{"LOCAL: global_sandbox\n(Global Linter/Pytest)"}
    end

    subgraph Phase4 ["Phase 4: UAT & QA Graph"]
        direction TB
        UatEval{"LOCAL: uat_evaluate\n(Playwright E2E Tests)"}
        UxAuditor["OpenRouter: ux_auditor\n(Multimodal UX Review)"]
        QaAuditor["OpenRouter: qa_auditor\n(Diagnostic Analysis)"]
        QaSession["JULES: qa_session\n(Integration Fixes)"]
    end

    Phase0 --> Phase1
    Phase1 --> Phase2
    Phase2 -- "All Cycles Done" --> MergeTry
    MergeTry -- "Conflict" --> MasterIntegrator
    MasterIntegrator --> MergeTry
    MergeTry -- "Success" --> GlobalSandbox
    GlobalSandbox -- "Pass" --> UatEval
    GlobalSandbox -- "Fail" --> MasterIntegrator
    UatEval -- "Fail" --> QaAuditor
    QaAuditor --> QaSession
    QaSession --> UatEval
    UatEval -- "Pass" --> UxAuditor
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

## Installation & Setup

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <your-repository>
   cd <your-repository>
   ```

2. Sync dependencies using uv:
   ```bash
   uv sync
   ```

3. Configure your core environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and populate your API keys
   ```

## Usage

### Initialize Project Requirements

For new or external projects, running `nitpick init` is the mandatory first step. It automatically scaffolds the required directory structure, initializes Git, and configures your environment.

```bash
uv run nitpick init
```
After initialization, edit `ALL_SPEC.md` and `USER_TEST_SCENARIO.md` inside the `dev_documents/` folder before running generation commands.

### Generate Development Cycles (Phase 1)
Parse your raw architectural documents into structured specifications and UAT plans.
```bash
uv run nitpick gen-cycles
```

### Run Full Orchestrated Pipeline (Phase 2, 3 & 4)
Execute the complete orchestrated 5-phase pipeline against your active project directory.
```bash
uv run nitpick run-pipeline
```

### Interactive Tutorials (UAT Verification)
To experience the fully automated, multi-modal User Acceptance Testing (UAT) pipeline interactively, you can run our definitive Marimo tutorial locally.
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
├── dev_documents/          # Auto-generated specs, UATs, architecture logs
│   ├── system_prompts/     # Cycle specific plans and documents
│   └── USER_TEST_SCENARIO.md
├── src/                    # The main implementation for NITPICKERS
│   ├── cli.py              # CLI entrypoint
│   ├── state.py            # Pydantic state models
│   ├── graph.py            # Main LangGraph declarations
│   ├── nodes/              # LangGraph node routing functions
│   ├── domain_models/      # Pydantic schemas
│   └── services/           # Orchestration (workflow.py) & Diff Logic (conflict_manager.py)
├── tests/                  # Unit, Integration, and UAT tests
├── tutorials/              # Marimo-based interactive tutorials
├── pyproject.toml          # Project configuration (Dependencies & Linting)
└── README.md               # User documentation
```

## License

MIT License
