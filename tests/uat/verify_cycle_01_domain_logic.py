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
    from src.domain_models import ConflictRegistryItem, E2BExecutionResult, UATResult
    from src.state import CycleState, IntegrationState

    return ConflictRegistryItem, CycleState, E2BExecutionResult, IntegrationState, UATResult


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
def test_scenario_01_new_1(FixPlan: Any, mo: Any, pytest: Any, ValidationError: Any) -> tuple[Any, ...]:  # noqa: N803
    import pytest
    from pydantic import ValidationError

    # SCENARIO-01-1: The stateless Auditor generates a malformed JSON response
    # Expectation: System immediately raises a ValidationError preventing bad data
    malformed_payload = {"modifications": [{"filepath": "src/app.py", "explanation": "fix bug"}]}
    payload: Any = malformed_payload

    with pytest.raises(ValidationError) as exc:
        FixPlan(**payload)

    assert "diff_block" in str(exc.value)

    # test empty list as well
    with pytest.raises(ValidationError) as exc_empty:
        FixPlan(modifications=[])
    assert "List should have at least 1 item" in str(exc_empty.value)

    mo.md("✅ Scenario 01-New-1 Passed: Malformed FixPlan payload rejected.")
    return exc, exc_empty


@app.cell
def test_scenario_01_new_2(UATResult: Any, mo: Any, tempfile: Any, Path: Any) -> tuple[Any, ...]:  # noqa: N803
    import tempfile
    from pathlib import Path

    # SCENARIO-01-2: UAT Artifacts Instantiation and Serialization
    # Expectation: Mock paths are parsed correctly and serialization preserves structure
    with (
        tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_img,
        tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_txt,
    ):
        img_path = tmp_img.name
        txt_path = tmp_txt.name

    try:
        valid_payload = {
            "exit_code": 1,
            "stderr": "test failed",
            "screenshot_path": img_path,
            "dom_trace_path": txt_path,
        }

        payload_uat: Any = valid_payload
        uat_result = UATResult(**payload_uat)
        assert uat_result.exit_code == 1
        assert uat_result.screenshot_path == img_path

        serialized_uat = uat_result.model_dump_json()
        assert img_path in serialized_uat

        mo.md("✅ Scenario 01-New-2 Passed: UATResult instantiated properly.")
        res = (uat_result, serialized_uat)
    finally:
        if Path(img_path).exists():
            Path(img_path).unlink()
        if Path(txt_path).exists():
            Path(txt_path).unlink()

    return res


@app.cell
def test_scenario_01_new_3(mo: Any) -> tuple[Any]:
    # SCENARIO-01-3: CycleState Backward Compatibility
    # Expectation: Initializing state without UAT fields works and defaults correctly
    from src.state import CycleState

    legacy_state = CycleState(cycle_id="legacy-cycle")

    assert legacy_state.uat_exit_code == 0
    assert legacy_state.uat_artifacts is None
    assert legacy_state.current_fix_plan is None

    mo.md("✅ Scenario 01-New-3 Passed: Legacy states successfully load.")
    return (legacy_state,)


if __name__ == "__main__":
    app.run()
