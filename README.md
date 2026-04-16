# NITPICKERS

An AI-Native Code Development Environment with Red Teaming built to deliver robust software through isolated parallel development phases and deterministic AI conflict resolution.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen) ![License](https://img.shields.io/badge/license-MIT-blue)

## Key Features

- **Automated Mechanical Blockade:** Zero-trust validation. Pull requests are explicitly blocked until all static (Ruff, Mypy) and dynamic (Pytest) structural checks pass with a zero exit code, eliminating assumed success.
- **5-Phase Parallel & Sequential Architecture:** Seamlessly orchestrates requirement decomposition, parallel feature implementation, 3-Way Diff integration, and full-system E2E UI testing in strict phases.
- **3-Way Git Merge Conflict System:** Intelligent conflict resolution system utilizing an AI Master Integrator. Automatically detects git conflicts, extracts Base, Local, and Remote file versions, and synthesizes a unified code block to guarantee seamless parallel branch integration.
- **Multi-Modal Diagnostic Capture:** Automatically capture rich UI failure context, including high-resolution screenshots and DOM traces via Playwright, providing undeniable evidence of frontend regressions.
- **Self-Healing Loop with Stateless Auditor:** Utilize advanced Vision LLMs (via OpenRouter) strictly as outer-loop diagnosticians. They analyze error artifacts without project context fatigue and return structured JSON fix plans to the Worker agent.

## Architecture Overview

NITPICKERS operates on a strict 5-Phase pipeline managed by LangGraph. Following initialization, the system architects the workload into independent cycles. Each cycle runs concurrently in an isolated environment, creating, evaluating, and refactoring code. Once all parallel threads conclude successfully, a central integration phase kicks in, merging all outcomes natively or via AI-driven conflict resolution. Finally, the system executes E2E QA checks in an integrated environment to secure deployment stability.

```mermaid
flowchart TD
    %% Phase 0: Init Phase (CLI Setup)
    subgraph Phase0 ["Phase 0: Init Phase (CLI Setup)"]
        direction TB
        InitCmd([CLI: nitpick init])
        GenTemplates[".env.sample / .gitignore, strict ruff, mypy settings (Local)"]
        UpdateDocker["add .env path on docker-compose.yml (User)"]
        PrepareSpec["define ALL_SPEC.md (User)"]

        InitCmd --> GenTemplates --> UpdateDocker --> PrepareSpec
    end

    %% Phase 1: Architect Graph
    subgraph Phase1 ["Phase 1: Architect Graph"]
        direction TB
        InitCmd2([CLI: nitpick gen-cycles])

        subgraph Architect_Phase ["JULES: Architect Phase"]
            ArchSession["architect_session\n(Requirement Decomposition)"]
            ArchCritic{"self-critic review\n(Fixed Prompt Plan Review)"}
        end

        OutputSpecs[/"Cycle SPEC.md\nGlobal UAT_SCENARIO.md"/]

        PrepareSpec --> InitCmd2 --> ArchSession
        ArchSession --> ArchCritic
        ArchCritic -- "Reject" --> ArchSession
        ArchCritic -- "Approve" --> OutputSpecs
    end

    %% Phase 2: Coder Graph
    subgraph Phase2 ["Phase 2: Coder Graph (Parallel: Cycle 1...N)"]
        direction TB
        CoderSession["JULES: coder_session\n(Implementation & PR)"]
        SelfCritic["JULES: SelfCriticReview\n(Initial Polish)"]
        SandboxEval{"LOCAL: sandbox_evaluate\n(Linter / Unit Test)"}

        AuditorNode{"OpenRouter: auditor_node\n(Serial: Auditor 1→2→3)"}
        RefactorNode["JULES: refactor_node\n(Fixed Prompt Refactor)"]
        FinalCritic{"JULES: Final Self-critic\n(Final Logic Verification)"}

        OutputSpecs -->|Start as Cycle N| CoderSession

        CoderSession -- "1st Iteration" --> SelfCritic --> SandboxEval
        CoderSession -- "2nd+ Iteration" --> SandboxEval

        SandboxEval -- "Fail" --> CoderSession
        SandboxEval -- "Pass (Implementing)" --> AuditorNode
        SandboxEval -- "Pass (Refactored)" --> FinalCritic

        AuditorNode -- "Reject (Max 2 Attempts)" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode

        RefactorNode --> SandboxEval

        FinalCritic -- "Reject" --> CoderSession
    end

    %% Phase 3: Integration Phase
    subgraph Phase3 ["Phase 3: Integration Phase"]
        direction TB
        MergeTry{"Local: Git PR Merge\n(Integrate to int branch)"}
        MasterIntegrator["JULES: master_integrator\n(3-Way Diff Conflict Resolution)"]
        GlobalSandbox{"LOCAL: global_sandbox\n(Global Linter/Pytest)"}
    end

    %% Phase 4: UAT & QA Graph
    subgraph Phase4 ["Phase 4: UAT & QA Graph"]
        direction TB
        UatEval{"LOCAL: uat_evaluate\n(Playwright E2E Tests)"}
        QaAuditor["OpenRouter: qa_auditor\n(Error Log/Vision Diagnostics)"]
        QaSession["JULES: qa_session\n(Integration Environment Fixes)"]
        EndNode(((END: Deployment Ready)))
    end

    %% Inter-Phase Transitions
    FinalCritic -- "Approve\n(All PRs Collected)" --> MergeTry

    MergeTry -- "Conflict" --> MasterIntegrator
    MasterIntegrator --> MergeTry

    MergeTry -- "Success" --> GlobalSandbox
    GlobalSandbox -- "Fail (Integration Bugs)" --> MasterIntegrator

    GlobalSandbox -- "Pass" --> UatEval

    UatEval -- "Fail" --> QaAuditor
    QaAuditor --> QaSession
    QaSession --> UatEval

    UatEval -- "Pass" --> EndNode

    %% Styling
    classDef conditional fill:#fff3cd,stroke:#ffeeba,stroke-width:2px;
    classDef success fill:#d4edda,stroke:#c3e6cb,stroke-width:2px;
    classDef highlight fill:#e1f5fe,stroke:#03a9f4,stroke-width:2px;

    class ArchCritic,SandboxEval,AuditorNode,FinalCritic,MergeTry,GlobalSandbox,UatEval conditional;
    class EndNode success;
    class GlobalSandbox highlight;
```

## Prerequisites

- Python >= 3.12, < 3.14
- `uv` Package Manager
- Docker
- Git
- API Keys (OPENROUTER_API_KEY, E2B_API_KEY, JULES_API_KEY)

## Installation & Setup

Ensure you have `uv` installed, then synchronize the environment:

```bash
git clone <repository_url>
cd nitpickers
uv sync
cp .env.example .env
# Edit .env to add required API Keys
```

## Usage

Start by initializing the current directory structure:
```bash
uv run nitpick init
```
*Note: This generates boilerplate definitions. You must customize `dev_documents/ALL_SPEC.md` prior to the next step.*

Generate development cycles automatically based on the specification:
```bash
uv run nitpick gen-cycles
```

Execute the full orchestration pipeline covering all 5 phases:
```bash
uv run nitpick run-pipeline
```

## Development Workflow

This codebase enforces strict code quality checks.

To format and lint your code:
```bash
uv run ruff check --fix
uv run ruff format
uv run mypy src
```

To run unit and integration testing (incorporating DB transaction rollbacks where applicable):
```bash
uv run pytest --cov=src --cov=dev_src
```

## Project Structure

```text
nitpickers/
├── dev_documents/
│   ├── system_prompts/   # Architectural design and Phase specifications (CYCLE01-CYCLE05)
│   ├── ALL_SPEC.md       # Target project specifications
│   └── required_envs.json
├── src/
│   ├── cli.py            # Typer command line entries & phase orchestration
│   ├── graph.py          # Phase definitions for Coder, Integration, and QA graphs
│   ├── state.py          # Typed definitions for CycleState & IntegrationState
│   ├── services/         # Core application services (e.g. Workflow, Conflict Manager)
│   └── nodes/            # Isolated LangGraph components and routing conditionals
├── tests/                # Unit and Integration test modules
└── tutorials/            # Marimo UAT scenarios
```

## License

MIT License