# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "marimo>=0.21.1",
#     "pydantic~=2.11.0"
# ]
# ///
import marimo

__generated_with = "0.21.1"
app = marimo.App()


@app.cell
def __():
    import marimo as mo
    intro = mo.md(
        """
        # Master Plan for User Acceptance Testing and Tutorials

        This interactive tutorial demonstrates the fully automated, multi-modal User Acceptance Testing (UAT) pipeline of the NITPICKERS framework.
        It supports both **Mock Mode** (for CI environments) and **Real Mode** (when proper API keys and LangSmith tracing are configured).

        Let's explore the phases of the UAT pipeline!
        """
    )
    return intro, mo


@app.cell
def __():
    import asyncio
    import os
    import tempfile
    from pathlib import Path

    import pytest

    # Mock Mode configuration
    os.environ["MOCK_LLM"] = "true"

    # Create a temporary directory for artifacts that automatically cleans up
    artifacts_temp_dir = tempfile.TemporaryDirectory()
    artifacts_path = Path(artifacts_temp_dir.name)

    return os, tempfile, pytest, Path, asyncio, artifacts_temp_dir, artifacts_path


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

    # Complete Mock Implementation of ProcessRunner matching exactly the expected interface
    class MockProcessRunner:
        async def run_command(
            self,
            cmd: list[str],
            cwd=None,
            check: bool = True,
            env=None,
            timeout=None,
        ) -> tuple[str, str, int, bool]:
            """
            Mock execution that simulates a deliberate failure on specific commands.
            Returns: (stdout, stderr, exit_code, timeout_occurred)
            """
            cmd_str = " ".join(cmd)
            if cmd_str == "python -c print('hello'":
                # Simulate a syntax error return
                return "", "  File \"<string>\", line 1\n    print('hello'\n                 ^\nSyntaxError: unexpected EOF while parsing", 1, False
            return "success", "", 0, False

    runner = MockProcessRunner()

    async def run_failing_command():
        # Using a deliberate syntax error with a bash command to simulate failing static check
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
    return MockProcessRunner, run_failing_command, exit_code, runner, stderr, stdout, timeout


@app.cell
def __(Path, artifacts_path, mo, os):
    mo.md("## Scenario 4: Multi-Modal Artifact Capture")

    # Include exact replica of MultiModalArtifact schema definition for guaranteed compatibility
    from pydantic import BaseModel, ConfigDict, model_validator

    class MultiModalArtifact(BaseModel):
        model_config = ConfigDict(extra="forbid")

        test_id: str
        screenshot_path: str
        trace_path: str | None = None
        console_logs: list[str]
        traceback: str

        @model_validator(mode="after")
        def _verify_file_paths(self) -> "MultiModalArtifact":
            """Verify that the paths for screenshot and trace exist."""
            if not Path(self.screenshot_path).exists():
                msg = f"Screenshot file not found: {self.screenshot_path}"
                raise ValueError(msg)
            if self.trace_path is not None and not Path(self.trace_path).exists():
                msg = f"Trace file not found: {self.trace_path}"
                raise ValueError(msg)
            return self

    # Create dummy files within the managed temporary directory
    dummy_screenshot = artifacts_path / "dummy_screenshot.png"
    dummy_screenshot.write_bytes(b"")

    dummy_trace = artifacts_path / "dummy_trace.zip"
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
    return BaseModel, ConfigDict, MultiModalArtifact, artifact, dummy_screenshot, dummy_trace, model_validator


@app.cell
def __(BaseModel, ConfigDict, artifact, mo):
    mo.md("## Scenario 5: The Auditor Recovery Loop")

    import json

    from pydantic import Field

    # Exact replica of FixPlanSchema
    class FixPlanSchema(BaseModel):
        """
        Structured JSON Fix Plan returned by the Stateless Auditor to the Worker.
        """
        model_config = ConfigDict(extra="forbid")

        target_file: str = Field(
            ..., description="The exact path of the file to modify to resolve the bug."
        )
        defect_description: str = Field(
            ..., description="A clear reasoning and explanation of the defect and the intended fix."
        )
        git_diff_patch: str = Field(
            ...,
            description="A precise structural modification instruction block, such as code snippets or a diff.",
        )

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
    return Field, FixPlanSchema, fix_plan, json, mock_auditor_json_response


if __name__ == "__main__":
    app.run()
