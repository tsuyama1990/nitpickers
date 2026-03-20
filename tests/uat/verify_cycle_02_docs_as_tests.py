from typing import Any

import marimo

__generated_with = "0.21.0"
app = marimo.App(width="medium")


@app.cell
def setup_imports() -> tuple[Any, ...]:
    import subprocess
    import tempfile
    import textwrap
    from pathlib import Path

    return subprocess, tempfile, textwrap, Path


@app.cell
def setup_mock_project(subprocess: Any, tempfile: Any, textwrap: Any, Path: Any) -> tuple[Any, ...]:  # noqa: N803
    # Setup test directory and mock ALL_SPEC.md
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)

    mock_spec_content = textwrap.dedent(
        """
        # Test Specification

        ## Valid Scenario
        ```python uat-scenario scenario_id="valid-01"
        assert True
        print("Valid scenario executed")
        ```

        ## Invalid Scenario
        ```python uat-scenario scenario_id="invalid-01"
        assert False, "Deliberate failure"
        ```
        """
    )

    spec_path = temp_path / "ALL_SPEC.md"
    spec_path.write_text(mock_spec_content)

    # Copy conftest.py logic to the temp dir so it works independently
    # Or just run pytest from the root, pointing to the temp dir.
    # Since we modified the root conftest.py, we can run `pytest /path/to/temp/ALL_SPEC.md`
    return temp_path, spec_path


@app.cell
def run_pytest(subprocess: Any, temp_path: Any, spec_path: Any, Path: Any) -> tuple[Any, ...]:  # noqa: N803
    import os
    import sys

    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd())

    # We run pytest against the temp spec_path
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(spec_path), "-v", "-p", "tests.conftest"],
        capture_output=True,
        text=True,
        cwd=str(temp_path),  # Run from the temp dir where ALL_SPEC.md is
        env=env,
    )

    print(result.stdout)  # noqa: T201
    print(result.stderr)  # noqa: T201
    return (result,)


@app.cell
def verify_scenario_1(result: Any) -> tuple[Any, ...]:
    # Scenario 1: Successful Markdown Test Execution
    assert "test_valid-01" in result.stdout
    assert "PASSED" in result.stdout or "passed" in result.stdout

    return (True,)


@app.cell
def verify_scenario_2(result: Any) -> tuple[Any, ...]:
    # Scenario 2: Markdown Test Failure Reporting
    assert "test_invalid-01" in result.stdout
    assert "FAILED" in result.stdout or "failed" in result.stdout
    assert "AssertionError: Deliberate failure" in result.stdout

    return (True,)


if __name__ == "__main__":
    app.run()
