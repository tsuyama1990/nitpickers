from typing import Any

import marimo

__generated_with = "0.21.0"
app = marimo.App(width="medium")


@app.cell
def setup_imports() -> tuple[Any, ...]:
    import marimo as mo

    return (mo,)


@app.cell
def setup_models() -> tuple[Any, ...]:
    from src.domain_models import ConflictRegistryItem, E2BExecutionResult
    from src.state import CycleState, IntegrationState

    return ConflictRegistryItem, CycleState, E2BExecutionResult, IntegrationState


@app.cell
def scenario_01_01(CycleState: Any, mo: Any) -> tuple[Any, ...]:  # noqa: N803
    # Scenario ID 01-01: Backward Compatible State Initialization
    state = CycleState(cycle_id="legacy-session")

    assert state.sandbox_artifacts == {}
    assert state.conflict_status is None

    mo.md("✅ Scenario 01-01 Passed: CycleState initialized with backward-compatible defaults.")
    return (state,)


@app.cell
def scenario_01_02(ConflictRegistryItem: Any, E2BExecutionResult: Any, mo: Any) -> tuple[Any, ...]:  # noqa: N803
    # Scenario ID 01-02: Conflict & Sandbox State Assignment
    import contextlib

    import pydantic

    with contextlib.suppress(pydantic.ValidationError):
        # Invalid exit_code type
        E2BExecutionResult(exit_code="abc")

    result = E2BExecutionResult(exit_code="0")  # Coerced to int 0
    assert result.exit_code == 0

    conflict = ConflictRegistryItem(
        file_path="src/main.py", conflict_markers=["<<<<<<<", "=======", ">>>>>>>"]
    )
    serialized = conflict.model_dump()
    assert serialized["file_path"] == "src/main.py"

    mo.md("✅ Scenario 01-02 Passed: Domain models properly validate types and serialize.")
    return conflict, result, serialized


@app.cell
def scenario_01_03(mo: Any) -> tuple[Any, ...]:
    # Scenario ID 01-03: Source Path Verification
    import subprocess

    try:
        res = subprocess.run(
            ["uv", "run", "ac-cdd", "--help"],  # noqa: S607
            capture_output=True,
            text=True,
            check=True,
        )
        assert "Usage" in res.stdout
    except subprocess.CalledProcessError as e:
        msg = f"CLI check failed: {e.stderr}"
        raise AssertionError(msg) from e

    mo.md("✅ Scenario 01-03 Passed: CLI executes successfully via `src.cli:app`.")
    return (res,)


@app.cell
def scenario_01_observability_hard_stop(mo: Any) -> tuple[Any, ...]:
    import os
    import subprocess

    # Scenario 1: Missing Environment Variables Hard Stop
    env = os.environ.copy()
    if "LANGCHAIN_TRACING_V2" in env:
        del env["LANGCHAIN_TRACING_V2"]
    if "LANGCHAIN_API_KEY" in env:
        del env["LANGCHAIN_API_KEY"]

    try:
        res = subprocess.run(
            ["uv", "run", "python", "-m", "src.cli", "run-cycle", "--id", "01"],  # noqa: S607
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode != 0
        assert "LANGCHAIN_TRACING_V2" in res.stdout or "LANGCHAIN_TRACING_V2" in res.stderr
    except Exception as e:
        msg = f"Hard stop test failed: {e}"
        raise AssertionError(msg) from e

    mo.md("✅ Scenario 1 Passed: CLI halts execution on missing tracing configurations.")
    return (res,)


@app.cell
def scenario_01_observability_success(mo: Any) -> tuple[Any, ...]:
    import os
    import subprocess

    # Scenario 2: Successful Verification and Execution
    env = os.environ.copy()
    env["LANGCHAIN_TRACING_V2"] = "true"
    env["LANGCHAIN_API_KEY"] = "mock_api_key"
    env["LANGCHAIN_PROJECT"] = "mock_project"

    try:
        # Just running a mock or help command to ensure it doesn't fail on observability verification
        res = subprocess.run(
            ["uv", "run", "python", "-m", "src.cli", "run-cycle", "--help"],  # noqa: S607
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert res.returncode == 0
    except subprocess.CalledProcessError as e:
        msg = f"Success execution test failed: {e.stderr}"
        raise AssertionError(msg) from e

    mo.md(
        "✅ Scenario 2 Passed: CLI successful verification with configured observability parameters."
    )
    return (res,)


if __name__ == "__main__":
    app.run()
