# USER TEST SCENARIO

## Tutorial Strategy

The primary goal of this User Acceptance Testing and Tutorial strategy is to transform the theoretical automated UAT pipeline and observability architecture into an interactive, executable learning experience. We will utilize **Marimo** to create a single, cohesive tutorial that actively demonstrates the core mechanical gates, the Stateless Auditor recovery loops, and the LangSmith observability integration.

### Mock Mode vs. Real Mode

To ensure the tutorial is accessible in any CI environment or for users without immediate access to E2B sandboxes or OpenRouter API keys, the tutorial must robustly support a **"Mock Mode"**.
- **Mock Mode**: By default, the tutorial runs offline. It uses `unittest.mock.patch` internally to simulate the Playwright multi-modal capture (generating a static dummy image) and the OpenRouter API response (yielding a hardcoded JSON Fix Plan). This allows users to understand the architectural flow and State dictionary mutations without incurring costs or managing complex environment setups.
- **Real Mode**: Users who configure their `.env` file with valid `OPENROUTER_API_KEY` and `LANGCHAIN_API_KEY` can toggle a setting within the Marimo notebook to execute the live Outer Loop. This mode triggers actual `ProcessRunner` execution, genuine Playwright browser automation, and live Vision LLM auditing.

## Tutorial Plan

A **SINGLE** Marimo Python file will be created to house all interactive scenarios.

**Target File:** `tutorials/automated_uat_pipeline.py`

### Scenario 1: The Observability Gate (Phase 0)
- **Objective**: Demonstrate the CLI's mechanical blockade when required LangSmith tracing variables are missing.
- **Execution**: The Marimo cell will attempt to initialize the `ManagerUseCase` with an empty environment configuration. It will visually assert that the system correctly raises the Hard Stop Prompt, proving the zero-trust initialization requirement.

### Scenario 2: Inner Loop Gatekeeping (Phase 1)
- **Objective**: Show how structural errors immediately block PR creation.
- **Execution**: The tutorial will dynamically generate a python file with an intentional type error. It will then execute the `ProcessRunner`'s validation step (`uv run mypy .`), capturing the non-zero exit code and illustrating how the state router redirects the flow back to the Stateful Worker.

### Scenario 3: Outer Loop Multi-Modal Capture (Phase 2)
- **Objective**: Verify that dynamic UI failures yield visual artifacts.
- **Execution**: Using Pytest and Playwright (mocked or live), the tutorial will run a failing test. It will visually render the generated screenshot and DOM trace directly within the Marimo notebook output, proving the successful capture of context for the Auditor.

### Scenario 4: Stateless Auditor & Surgical Recovery (Phase 3)
- **Objective**: Demonstrate the OpenRouter Vision LLM outputting a structured Pydantic Fix Plan.
- **Execution**: The tutorial will feed the artifacts from Scenario 3 into the `AuditorUseCase`. It will display the raw JSON Fix Plan output and demonstrate how it is parsed seamlessly into the `FixPlan` Pydantic model for the Worker to consume.

## Tutorial Validation

The Marimo tutorial file (`tutorials/automated_uat_pipeline.py`) must be executed end-to-end to validate that all cells run without syntax errors and that the `Mock Mode` correctly simulates the pipeline behavior.

Validation Command:
```bash
uv run marimo test tutorials/automated_uat_pipeline.py
```
The execution must complete successfully, confirming that the UAT pipeline concepts are fully verifiable by the end user.