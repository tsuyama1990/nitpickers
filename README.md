# NITPICKERS

An AI-native development environment based on a highly robust methodology designed to enforce absolute zero-trust validation of AI-generated code. NITPICKERS uses static analysis, dynamic testing in a secure sandbox, and automated red team auditing to ensure that generated code meets professional engineering standards.

## Core Features

- **Concurrent Execution & Architecture Generation:** Automatically split and manage complex applications by locking feature cycles with tight structural constraints.
- **Zero-Trust Validation:** All code goes through `ruff` and `mypy` static checks followed by a full dynamic execution of user acceptance tests in a secure E2B sandbox environment.
- **Automated Refactoring:** Global AST-based analysis identifies DRY violations, reducing duplicated code seamlessly and ensuring high-quality, readable repositories.
- **Self-Healing Loop:** Test failures dynamically generate traceback logs and direct the AI to autonomously fix issues without manual developer intervention.

## Requirements

Ensure the following tools are available on your system:
- `uv` - The fastest Python package installer and resolver.
- `git` - Version control for your codebase.

You will also need valid API keys for LLM reasoning and the E2B sandbox environment. Set them in a `.env` file or export them locally:
- `JULES_API_KEY`
- `E2B_API_KEY`
- `OPENROUTER_API_KEY` (Optional, if using custom fast models for auditing)

## Installation

Getting started with NITPICKERS is easy. Make sure you have `uv` installed.

1. Clone the repository and change the directory:
   ```bash
   git clone <your-repository>
   cd <your-repository>
   ```

2. Sync the dependencies and initialize the virtual environment:
   ```bash
   uv sync
   ```

## Usage

NITPICKERS operates mostly through its command-line interface.

To run the entire development pipeline automatically, covering requirement planning, parallel implementation, auditing, test verification, global refactoring, and PR generation:

```bash
uv run python src/cli.py generate <number_of_cycles> --auto-run
```

If you prefer a step-by-step approach, you can generate your architecture and then execute your cycles manually:

1. **Architecture & Cycle Generation**
   ```bash
   uv run python src/cli.py generate 5
   ```
   *This plans 5 cycles and produces specifications and test scenarios.*

2. **Execute a Cycle**
   ```bash
   uv run python src/cli.py run <cycle_id>
   ```
   *E.g. run `01` to start implementation of Cycle 01.*

3. **Global Refactor & Finalize**
   ```bash
   uv run python src/cli.py finalize
   ```
   *Resolves structural redundancy and runs final UATs before creating a PR.*

## Directory Structure

```
/
├── dev_documents/          # Auto-generated specs, UATs, logs
├── src/                    # The main implementation for NITPICKERS
│   ├── cli.py              # CLI entrypoint
│   ├── domain_models/      # Pydantic schemas enforcing interface locks
│   ├── nodes/              # LangGraph workflow nodes
│   ├── services/           # Business logic and external API integrations
│   └── tests/              # E2E and unit tests
├── pyproject.toml          # Project configuration
└── README.md               # User documentation
```
