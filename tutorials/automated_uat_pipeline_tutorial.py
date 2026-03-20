# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.21.1",
# ]
# ///
import marimo

__generated_with = "0.10.14"
app = marimo.App()


@app.cell
def __():
    import marimo as mo
    return mo.md(
        """
        # Master Plan for User Acceptance Testing and Tutorials

        This interactive tutorial demonstrates the fully automated, multi-modal User Acceptance Testing (UAT) pipeline of the NITPICKERS framework.
        It supports both **Mock Mode** (for CI environments) and **Real Mode** (when proper API keys and LangSmith tracing are configured).

        Let's explore the phases of the UAT pipeline!
        """
    ),


@app.cell
def __():
    import os
    import pytest
    from pathlib import Path
    import asyncio

    # Mock Mode configuration
    os.environ["MOCK_LLM"] = "true"

    # Ensure artifacts directory exists for later scenarios
    os.makedirs("artifacts", exist_ok=True)
    return os, pytest, Path, asyncio


@app.cell
def __(os, mo):
    mo.md("## Scenario 1: Quick Start & Observability Gate Verification")

    import sys

    # Mocking config variables to simulate behavior
    class MockConfig:
        def __init__(self, has_langsmith: bool):
            self.has_langsmith = has_langsmith

        def verify_environment_and_observability(self):
            if not self.has_langsmith:
                raise ValueError("Environment & Observability Verification Failed: Missing LangSmith configuration.")
            return True

    # Simulate Missing Configuration
    missing_config = MockConfig(has_langsmith=False)

    try:
        missing_config.verify_environment_and_observability()
        result_1 = "Success (Unexpected)"
    except ValueError as e:
        result_1 = f"Hard Stop Triggered: {e}"

    # Simulate Valid Configuration
    valid_config = MockConfig(has_langsmith=True)
    try:
        valid_config.verify_environment_and_observability()
        result_2 = "Success: Environment Verified!"
    except ValueError as e:
        result_2 = f"Failed (Unexpected): {e}"

    mo.md(
        f"""
        **Missing Config Result:** `{result_1}`

        **Valid Config Result:** `{result_2}`
        """
    )
    return MockConfig, missing_config, result_1, valid_config, result_2, sys


@app.cell
def __(mo, pytest):
    mo.md("## Scenario 2: Docs-as-Tests Execution")

    # Simulate extracting a test block from a markdown string
    mock_markdown = '''
    # Feature X

    This feature does Y.

    ```python uat-scenario
    def test_feature_x():
        assert True
    ```
    '''

    import re

    def extract_uat_scenarios(markdown_text):
        pattern = r"```python uat-scenario\n(.*?)\n```"
        return re.findall(pattern, markdown_text, re.DOTALL)

    extracted_code = extract_uat_scenarios(mock_markdown)

    mo.md(
        f"""
        Extracted UAT Scenario Code from Markdown:

        ```python
        {extracted_code[0]}
        ```

        *In a real execution, custom Pytest hooks parse this dynamically and yield native Pytest items.*
        """
    )
    return extract_uat_scenarios, extracted_code, mock_markdown, re


@app.cell
def __(asyncio, mo, os):
    mo.md("## Scenario 3: Mechanical Blockade (Static & Dynamic)")

    from src.process_runner import ProcessRunner

    runner = ProcessRunner()

    async def run_failing_command():
        # Using a deliberate syntax error with a bash command to simulate failing static check
        # We use python -c with a syntax error
        return await runner.run_command(["python", "-c", "print('hello'"], check=False)

    stdout, stderr, exit_code, timeout = asyncio.run(run_failing_command())

    mo.md(
        f"""
        **Command Run:** `python -c "print('hello'"`

        **Exit Code:** `{exit_code}`

        **Stderr Captured:** `{stderr}`

        *The ProcessRunner captures the non-zero exit code, blocking PR creation and routing this standard error trace back to the Coder agent.*
        """
    )
    return ProcessRunner, run_failing_command, exit_code, runner, stderr, stdout, timeout


@app.cell
def __(Path, mo, os):
    mo.md("## Scenario 4: Multi-Modal Artifact Capture")

    # We simulate the generation of the MultiModalArtifact
    from src.domain_models.multimodal_artifact_schema import MultiModalArtifact

    # Create dummy files for the mock artifact
    dummy_screenshot = Path("artifacts/dummy_screenshot.png")
    dummy_screenshot.write_bytes(b"")

    dummy_trace = Path("artifacts/dummy_trace.zip")
    dummy_trace.write_bytes(b"")

    artifact = MultiModalArtifact(
        test_id="test_dummy_failure",
        screenshot_path=str(dummy_screenshot),
        trace_path=str(dummy_trace),
        console_logs=["Error: Element not found"],
        traceback="TimeoutError: locator.click() timed out"
    )

    mo.md(
        f"""
        Captured Artifact Details:

        - **Test ID:** `{artifact.test_id}`
        - **Screenshot Path:** `{artifact.screenshot_path}`
        - **Trace Path:** `{artifact.trace_path}`
        - **Console Logs:** `{artifact.console_logs}`

        *In real execution, `pytest-playwright` hooks automatically populate this on test failure.*
        """
    )
    return MultiModalArtifact, artifact, dummy_screenshot, dummy_trace


@app.cell
def __(artifact, mo):
    mo.md("## Scenario 5: The Auditor Recovery Loop")

    from src.domain_models.fix_plan_schema import FixPlanSchema
    import json

    # Simulate Stateless Auditor response (Mock Mode)
    mock_auditor_json_response = {
        "target_file": "src/frontend/button.py",
        "defect_description": "The 'Submit' button selector was changed, causing the test to timeout.",
        "git_diff_patch": "<<<<<<< SEARCH\nbutton_selector = '#submit-btn'\n=======\nbutton_selector = '#new-submit-btn'\n>>>>>>> REPLACE"
    }

    # Validate against our strict schema contract
    fix_plan = FixPlanSchema(**mock_auditor_json_response)

    mo.md(
        f"""
        Auditor Diagnostic Result (Validated via `FixPlanSchema`):

        - **Target File:** `{fix_plan.target_file}`
        - **Defect Description:** `{fix_plan.defect_description}`

        **Git Diff Patch to route back to Worker:**
        ```
        {fix_plan.git_diff_patch}
        ```
        """
    )
    return FixPlanSchema, fix_plan, json, mock_auditor_json_response


if __name__ == "__main__":
    app.run()