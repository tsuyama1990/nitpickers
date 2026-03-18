# User Test Scenario & Tutorial Plan

## Aha! Moment
The "Magic Moment" occurs when a developer types `ac-cdd run-cycle --id all --parallel` and witnesses 6 to 8 AI development sessions running perfectly in parallel without stepping on each other's toes. The CLI renders a real-time terminal UI showing multiple progress bars as each cycle is planned, tested (via the E2B sandbox in the cloud), implemented, audited by the Red Team, and then automatically resolves complex Git merge conflicts semantically. Within minutes, a massive feature set that would take human engineers weeks to coordinate is safely merged, statically verified by `mypy`/`ruff`, and 100% dynamically verified by `pytest` — resulting in a perfectly clean, refactored `main` branch ready for production.

## Prerequisites
- **Python 3.12+** and `uv` package manager installed locally.
- **Docker Desktop** installed and running (to host the isolated `ac-cdd` container).
- **API Keys:**
  - `JULES_API_KEY` or `OPENROUTER_API_KEY` (for the AI Planner, Coder, and Red Team Auditor).
  - `E2B_API_KEY` (for the cloud-based Sandbox execution of UAT tests).
  - `GITHUB_TOKEN` (for Git operations and PR generation).

## Success Criteria
- The user can run the `marimo` tutorial notebook from start to finish.
- The tutorial successfully spins up the `ac-cdd` container or CLI.
- The tutorial initiates the `gen-cycles` to produce the architecture docs.
- The tutorial initiates the parallel `run-cycle`, visually showing concurrent execution and E2B validation.
- The final result is a passing `pytest` suite, clean `ruff`/`mypy` checks, and a merged codebase that correctly implements the requirements originally specified in `ALL_SPEC.md`.

## Tutorial Strategy
To provide the best user experience and a verifiable execution environment, the tutorial will be built as an interactive **Marimo** notebook.
- **Mock Mode vs. Real Mode:**
  - **Mock Mode (CI/CD):** If API keys are absent, the tutorial will demonstrate the workflow using mock LangGraph states to show how the parallel execution and conflict resolution *would* behave.
  - **Real Mode:** When valid API keys are provided in `.ac_cdd/.env`, the notebook will actually instantiate the core `ac-cdd` CLI commands via `subprocess`, stream the output back to the Marimo UI, and execute the full NITPICKERS workflow on a sample `ALL_SPEC.md` payload.

## Tutorial Plan
A single interactive Marimo notebook will be generated to serve as the master tutorial and testing artifact.

**Target File:** `tutorials/nitpickers_concurrent_development_demo.py`

This file will contain:
1. **Introduction Block:** Explaining the AC-CDD upgrade, the concept of Zero-Trust Validation, and Concurrent Execution.
2. **Environment Setup Block:** Checks for required dependencies (`uv`, `docker`) and validates `.env` secrets.
3. **Architecture Generation Block:** Programmatically writes a minimal `ALL_SPEC.md` and triggers `ac-cdd gen-cycles`. Displays the resulting DAG of the cycles generated.
4. **Concurrent Execution Block:** The core demonstration. Executes `ac-cdd run-cycle --id all --parallel`. Uses Marimo's interactive output to stream logs of the Coder, Red Team Auditor, and E2B Executor happening simultaneously.
5. **Conflict Resolution & Refactor Block:** Highlights the Master Integrator Session resolving intentional conflicts, followed by the Global Refactor node cleaning up the AST.
6. **Validation Block:** Runs `pytest`, `ruff`, and `mypy` locally against the finalized output to prove the AI's work is 100% verified.

## Tutorial Validation
The system will run `uv run marimo run tutorials/nitpickers_concurrent_development_demo.py` to assert that the file is syntactically valid and executes without Python tracebacks. In a CI environment, this step ensures the tutorial remains functional as the underlying API evolves.
