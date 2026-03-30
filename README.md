# NITPICKERS

An AI-native development environment based on a highly robust methodology designed to enforce absolute zero-trust validation of AI-generated code. NITPICKERS utilizes static analysis, dynamic testing in a secure sandbox, and automated red team auditing across a rigorous 5-Phase framework to ensure that generated code meets professional engineering standards.

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Ruff](https://img.shields.io/badge/Ruff-Passed-success)
![Mypy](https://img.shields.io/badge/Mypy-Passed-success)
![Pytest](https://img.shields.io/badge/Pytest-Passed-success)

## Key Features

- **Automated Mechanical Blockade:** Zero-trust validation. Pull requests are explicitly blocked until all static (Ruff, Mypy) and dynamic (Pytest) structural checks pass with a zero exit code, eliminating assumed success.
- **5-Phase Parallel & Sequential Architecture:** Seamlessly orchestrates requirement decomposition, parallel feature implementation, 3-Way Diff integration, and full-system E2E UI testing.
- **Multi-Modal Diagnostic Capture:** Automatically captures rich UI failure context, including high-resolution screenshots and DOM traces via Playwright, providing undeniable evidence of frontend regressions.
- **Self-Healing Loop with Stateless Auditor:** Utilizes advanced Vision LLMs strictly as outer-loop diagnosticians. They analyze error artifacts without project context fatigue and return structured JSON fix plans to the Worker agent.
- **Intelligent 3-Way Diff Integration:** Safely resolves complex Git merge conflicts by isolating Base, Local, and Remote file versions into context-rich LLM prompts instead of relying on confusing standard conflict markers.

## Architecture Overview

The system operates across 5 distinct phases to guarantee code quality from planning to final integration.

```mermaid
flowchart TD
    subgraph Phase0 ["Phase 0: Init Phase"]
        direction TB
        InitCmd([CLI: nitpick init])
    end

    subgraph Phase1 ["Phase 1: Architect Graph"]
        direction TB
        InitCmd2([CLI: nitpick gen-cycles])
        ArchSession["JULES: architect_session"]
        ArchCritic{"JULES: self_critic"}
        InitCmd2 --> ArchSession
        ArchSession --> ArchCritic
        ArchCritic -- "Reject" --> ArchSession
    end

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

    subgraph Phase3 ["Phase 3: Integration Phase"]
        direction TB
        MergeTry{"Local: Git PR Merge"}
        MasterIntegrator["JULES: master_integrator (3-Way Diff)"]
        GlobalSandbox{"LOCAL: global_sandbox"}

        MergeTry -- "Conflict" --> MasterIntegrator
        MasterIntegrator --> MergeTry
        MergeTry -- "Success" --> GlobalSandbox
    end

    subgraph Phase4 ["Phase 4: UAT & QA Graph"]
        direction TB
        UatEval{"LOCAL: uat_evaluate"}
        QaAuditor["OpenRouter: qa_auditor"]
        QaSession["JULES: qa_session"]

        UatEval -- "Fail" --> QaAuditor
        QaAuditor --> QaSession
        QaSession --> UatEval
    end

    Phase0 --> Phase1
    Phase1 --> Phase2
    Phase2 -- "All Complete" --> MergeTry
    GlobalSandbox -- "Pass" --> UatEval
```

## Prerequisites

Ensure the following tools are available on your system:
- `Python` 3.12+
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

2. Sync dependencies using `uv`:
   ```bash
   uv sync
   ```

3. Configure your core environment variables (Tool-Level):
   ```bash
   cp .env.example .env
   # Edit .env and populate your JULES_API_KEY, E2B_API_KEY, OPENROUTER_API_KEY.
   ```

## Usage

For new or external projects, running `nitpick init` is the mandatory first step. It automatically scaffolds the required directory structure, initializes Git, and configures your environment.

### Quick Start Example

```bash
# 1. Initialize a new target project directory
mkdir my-target-project && cd my-target-project
nitpick init

# 2. Fill in dev_documents/ALL_SPEC.md with your requirements

# 3. Generate development cycles (Phase 1)
nitpick gen-cycles

# 4. Run Full Orchestrated Pipeline (Phase 2, 3 & 4)
nitpick run-pipeline
```

### Interactive Tutorials
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
