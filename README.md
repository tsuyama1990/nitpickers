# Nitpickers

![Build Status](https://img.shields.io/badge/build-passing-brightgreen) ![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

Nitpickers is an AI-native, multi-agent code development environment employing an autonomous "5-Phase Architecture" to decompose requirements, implement features in parallel, integrate conflicts, and enforce end-to-end user acceptance testing (UAT).

## Key Features

*   **Autonomous 5-Phase Workflow**: Distinct pipeline separating planning, coding, integration, and final testing, preventing "God Class" AI agents.
*   **Sequential Auditing & Refactoring**: Dedicated red-teaming loops (Auditor 1 -> 2 -> 3) and a final refactoring loop ensure code is safe and maintainable before integration.
*   **AI-Assisted 3-Way Diff Integration**: Intelligent conflict resolution that analyzes the Base, Branch A, and Branch B to safely merge parallel development cycles.
*   **Automated E2E Remediation**: Separated UAT Graph that runs final verifications and auto-heals bugs discovered in the global integrated environment.

## Architecture Overview

Nitpickers employs `LangGraph` to route states through five distinct phases, isolating responsibilities to ensure stability.

```mermaid
flowchart TD
    %% Phase0: Init Setup (CLI)
    subgraph Phase0 ["Phase 0: Init Phase (CLI Setup)"]
        direction TB
        InitCmd([CLI: nitpick init])
        GenTemplates[".env.sample / .gitignore, strict ruff, mypy settings"]

        InitCmd --> GenTemplates
    end

    %% Phase1: Architect Graph
    subgraph Phase1 ["Phase 1: Architect Phase"]
        direction TB
        InitCmd2([CLI: nitpick gen-cycles])
        ArchSession["architect_session\n(Splits requirements)"]
        OutputSpecs[/"CYCLE SPEC.md"/]

        InitCmd2 --> ArchSession --> OutputSpecs
    end

    %% Phase2: Coder Graph
    subgraph Phase2 ["Phase 2: Coder Phase (Parallel Cycles)"]
        direction TB
        CoderSession["JULES: coder_session"]
        SandboxEval{"LOCAL: sandbox_evaluate"}
        AuditorNode{"OpenRouter: auditor_node\n(1→2→3)"}
        RefactorNode["JULES: refactor_node"]

        CoderSession --> SandboxEval
        SandboxEval -- "Pass" --> AuditorNode
        AuditorNode -- "Reject" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode
        RefactorNode --> SandboxEval
    end

    %% Phase3: Integration Phase
    subgraph Phase3 ["Phase 3: Integration Phase"]
        direction TB
        MergeTry{"Local: Git PR Merge"}
        MasterIntegrator["JULES: master_integrator\n(3-Way Diff)"]
    end

    %% Phase4: UAT & QA Graph
    subgraph Phase4 ["Phase 4: UAT & QA Phase"]
        direction TB
        UatEval{"LOCAL: uat_evaluate"}
        QaSession["JULES: qa_session"]
    end

    Phase1 --> Phase2
    Phase2 --> Phase3
    MergeTry -- "Conflict" --> MasterIntegrator --> MergeTry
    Phase3 --> Phase4
    UatEval -- "Fail" --> QaSession --> UatEval
```

## Prerequisites

*   Python 3.12+
*   `uv` (Python package manager)
*   Docker & Docker Compose (for containerized execution)
*   API Keys: `JULES_API_KEY`, `OPENROUTER_API_KEY`, `E2B_API_KEY`

## Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/your-org/nitpickers.git
    cd nitpickers
    ```

2.  **Sync Dependencies using `uv`**
    ```bash
    uv sync
    ```

3.  **Configure Environment**
    ```bash
    cp .env.example .env
    # Edit .env and insert your API keys
    ```

## Usage

### Quick Start

1.  **Initialize the Project**
    ```bash
    uv run nitpick init
    ```

2.  **Generate Architecture and Cycle Plans** (Phase 1)
    ```bash
    uv run nitpick gen-cycles
    ```

3.  **Run the Full Pipeline** (Phase 2 to 4)
    ```bash
    uv run nitpick run-pipeline
    ```

### Interactive Tutorials

To understand the system flow or run it in a mocked CI environment, execute the interactive Marimo notebook:
```bash
uv run marimo edit tutorials/UAT_AND_TUTORIAL.py
```

## Development Workflow

*   **Running Tests**: `uv run pytest`
*   **Running Linters**: `uv run ruff check` and `uv run mypy src`
*   The project enforces a strict separation of concerns; when modifying LangGraph nodes, ensure they are thoroughly isolated and unit tested using mocked states.

## Project Structure

```text
nitpickers/
├── dev_documents/         # Architecture definitions and specifications
├── src/                   # Main application code
│   ├── graph.py           # LangGraph definitions
│   ├── state.py           # Pydantic state models
│   ├── services/          # Core orchestration and managers
│   └── nodes/             # Individual LLM/Execution nodes
├── tests/                 # Unit and Integration test suite
└── tutorials/             # Marimo notebooks for UAT
```

## License

MIT License. See `LICENSE` for details.
