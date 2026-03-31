# NITPICKERS: AI-Native Zero-Trust Development Environment

NITPICKERS is a state-of-the-art, AI-native software development environment architected from the ground up to enforce absolute zero-trust validation of automatically generated program code. By orchestrating a rigorous 5-phase execution pipeline, NITPICKERS utilizes static analysis, dynamic sandbox testing, serial red team auditing, and intelligent 3-Way Diff integration to guarantee that all AI-synthesized code meets uncompromising professional engineering standards before it ever reaches your main branch.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Ruff](https://img.shields.io/badge/Ruff-Passed-success)
![Mypy](https://img.shields.io/badge/Mypy-Passed-success)
![Pytest](https://img.shields.io/badge/Pytest-Passed-success)

## Key Features

- **Automated Mechanical Blockade (Zero-Trust):** Pull requests and code integrations are explicitly and unconditionally blocked until all static (Ruff, Mypy) and dynamic (Pytest) structural checks pass with an absolute zero exit code. There is no assumed success.
- **5-Phase Parallel & Sequential Architecture:** The system seamlessly, deterministically orchestrates complex requirement decomposition, massively parallel feature implementation, advanced 3-Way Diff conflict resolution, and exhaustive, full-system E2E UI testing.
- **Serial Red Team Auditing:** Code must survive a grueling, sequential review process conducted by multiple, entirely independent Auditor agents. This stateless auditing eliminates historical bias and ensures absolute logical correctness.
- **Intelligent 3-Way Diff Integration:** Instead of failing on complex branch collisions, a dedicated Master Integrator agent mathematically analyzes the Base, Local, and Remote file states to synthesize perfectly unified code blocks.
- **Multi-Modal Diagnostic Automation:** The system automatically captures rich UI failure context, including high-resolution Playwright screenshots and DOM traces, routing them to Vision LLMs for completely autonomous, self-healing remediation.

## Architecture Overview

The NITPICKERS system operates across 5 meticulously designed, distinct phases to mathematically guarantee code quality from the initial planning stages to final, global integration.

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
        ArchCritic{"JULES: architect_critic\n(Red Team Self-Critic)"}
        InitCmd2 --> ArchSession
        ArchSession --> ArchCritic
        ArchCritic -- "Reject" --> ArchSession
    end

    %% Phase2: Coder Graph (Parallel: Cycle 1...N)
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
        SandboxEval -- "Pass" --> AuditorNode
        AuditorNode -- "Reject" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode
        RefactorNode --> SandboxEval
        SandboxEval -- "Pass (Post-Refactor)" --> FinalCritic
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

Ensure the following critical tools are securely installed and available within your system environment:
- `python 3.12+`
- `uv` - The blazingly fast Python package installer and dependency resolver.
- `git` - Distributed version control for your codebase.
- `Docker` - (Highly Recommended for secure sandbox execution and Sidecar configuration).
- Valid, active API keys (must be configured in `.env`):
    - `JULES_API_KEY` (Primary Worker/Architect)
    - `E2B_API_KEY` (Secure Sandbox Execution)
    - `OPENROUTER_API_KEY` (Serial Auditors/Vision Models)

## Installation & Setup

The primary and highly recommended method for utilizing NITPICKERS is via Docker, operating efficiently in a secure "Sidecar" workflow. This allows you to mount any target project directory directly into the tool's container to seamlessly audit, build, and interact with external codebases without contaminating your local environment.

1. Clone the repository and navigate strictly to the project directory:
   ```bash
   git clone https://github.com/your-org/nitpickers.git
   cd nitpickers
   ```

2. Configure your core environmental secrets (Tool-Level):
   ```bash
   cp .env.example .env
   # Edit .env and meticulously populate your JULES_API_KEY, E2B_API_KEY, and OPENROUTER_API_KEY.
   # These tool-level infrastructure keys MUST stay within the isolated nitpickers directory.
   ```

3. Initialize the Environment:
   ```bash
   uv sync
   bash setup.sh
   source ~/.bashrc
   ```
   The `setup.sh` script will automatically construct the container and intelligently inject a `nitpick` alias into your `~/.bashrc`, enabling ubiquitous CLI access.

## Usage

Once your core `.env` is securely configured and the setup script has successfully completed, you can navigate to *any* external project directory and utilize the highly powerful `nitpick` command seamlessly.

### Initialize Project Requirements (Phase 0)

For all new or external target projects, running `nitpick init` is an absolute, mandatory first step. It automatically scaffolds the strictly required directory structure (`src/`, `tests/`, `dev_documents/`), intelligently initializes Git, and perfectly configures your strict linting environment.

```bash
cd /path/to/target/project
nitpick init
```
After successful initialization, meticulously fill in `dev_documents/ALL_SPEC.md` before executing generation commands.

### Generate Development Cycles (Phase 1)
Navigate to your active target project and systematically parse your raw architectural documents into highly structured specifications and rigorous UAT plans.
```bash
nitpick gen-cycles
```

### Run Full Orchestrated Pipeline (Phases 2, 3 & 4)
Execute the complete, highly orchestrated 5-phase pipeline against your currently active project directory. This command automatically and flawlessly manages parallel code implementation, strict serial auditing, 3-Way Diff integration, and final End-to-End validation.
```bash
nitpick run-pipeline
```

### Interactive Tutorials (UAT Verification)
To intimately experience the fully automated, zero-trust User Acceptance Testing (UAT) pipeline interactively, you can run our definitive, highly complex Marimo tutorial locally.
```bash
uv run marimo edit tutorials/UAT_AND_TUTORIAL.py
```

## Development Workflow

To ensure the architectural integrity of the NITPICKERS tool itself, strictly adhere to the following rigorous development commands:

-   **Run Strict Linters & Type Checks:**
    ```bash
    uv run ruff check .
    uv run mypy .
    ```
-   **Run Exhaustive Unit & Integration Tests (with Coverage):**
    ```bash
    uv run pytest
    ```

## Project Structure

```text
/
├── dev_documents/          # Auto-generated specifications, UAT scenarios, and system architecture plans
│   ├── system_prompts/     # Cycle specific operational plans and Pydantic schemas
│   ├── USER_TEST_SCENARIO.md
│   └── required_envs.json
├── src/                    # The highly robust core implementation for NITPICKERS
│   ├── cli.py              # Centralized CLI entrypoint
│   ├── state.py            # Strictly typed Pydantic state models (CycleState, IntegrationState)
│   ├── graph.py            # Complex LangGraph deterministic declarations
│   ├── nodes/              # Advanced LangGraph conditional routing logic
│   └── services/           # Orchestrator (workflow.py) & 3-Way Diff Logic (conflict_manager.py)
├── tests/                  # Exhaustive Unit, Integration, and UAT test suites
├── tutorials/              # Marimo-based interactive, executable tutorials
├── pyproject.toml          # Strict Project configuration (Dependencies & Linting rules)
└── README.md               # User documentation and architectural overview
```

## License

MIT License
