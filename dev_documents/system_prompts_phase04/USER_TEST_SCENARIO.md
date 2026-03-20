# Master Plan for User Acceptance Testing and Tutorials

## Tutorial Strategy

The objective is to transform the complex UAT pipeline features into an accessible, interactive, and reproducible tutorial experience for new users and developers. This will be achieved by leveraging the Marimo framework to create a single, comprehensive interactive notebook.

This notebook will serve a dual purpose: it will act as the definitive User Acceptance Test (UAT) for the newly implemented pipeline features, and it will serve as the primary educational resource.

To ensure the tutorial is robust and universally executable, we will implement a strategy supporting both "Mock Mode" and "Real Mode".
*   **Mock Mode (CI/no-api-key execution)**: By default, or when specific environment variables (like `MOCK_LLM=true`) are set, the tutorial will execute using dependency injection and mocked API responses. This allows users to verify the structural integrity of the pipeline (e.g., node routing, artifact capture logic, schema validation) without requiring paid API keys for OpenRouter or Gemini. It ensures the tutorial can run flawlessly in Continuous Integration environments.
*   **Real Mode**: When configured with valid API keys and LangSmith tracing variables, the tutorial will execute end-to-end calls against the actual LLMs and the local sandbox environment. This mode demonstrates the true power of the pipeline, showcasing real-time visual diagnostics and self-healing capabilities.

## Tutorial Plan

A **SINGLE** Marimo Text/Python file will be created to house all scenarios, ensuring simplicity and ease of use.

**Target File:** `tutorials/automated_uat_pipeline_tutorial.py`

This file will contain the following scenarios:

1.  **Quick Start & Observability Gate Verification**: Demonstrates the Phase 0 setup. It will simulate a missing LangSmith configuration to show the "hard stop" mechanical blockade, then proceed with a valid (mocked) configuration to show successful initialization.
2.  **Docs-as-Tests Execution**: Demonstrates Phase 1. It will load a mock markdown string containing a Python code block and execute it directly via the custom Pytest hook logic, proving the "translation gap" is eliminated.
3.  **Mechanical Blockade (Static & Dynamic)**: Demonstrates Phase 1. It will simulate a code failure (e.g., a deliberate syntax error) and show how the `ProcessRunner` captures the non-zero exit code and definitively routes the execution back to the Coder agent, preventing PR creation.
4.  **Multi-Modal Artifact Capture**: Demonstrates Phase 2. It will execute a headless Playwright test designed to fail, and visually display (within the Marimo notebook) the resulting screenshot and trace path that were automatically saved to the `artifacts/` directory.
5.  **The Auditor Recovery Loop**: Demonstrates Phase 3. It will pipe the captured multi-modal artifact from the previous step into the `auditor_usecase`. Using "Mock Mode," it will simulate a valid OpenRouter JSON response, validate it against the `FixPlanSchema`, and display the resulting routing decision.

## Tutorial Validation

Validation of this tutorial involves running the Marimo file in both "Mock Mode" and "Real Mode" (where possible) to ensure:
*   The Marimo application executes from start to finish without unhandled exceptions.
*   All markdown descriptions render correctly and clearly explain the underlying mechanics.
*   The mocked components accurately reflect the intended behavior of the real pipeline modules.
*   In Real Mode, the generated artifacts (screenshots, LangSmith traces) are correctly produced and visible.
