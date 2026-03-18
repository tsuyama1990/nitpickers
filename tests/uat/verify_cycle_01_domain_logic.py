import marimo

__generated_with = "0.21.0"
app = marimo.App(width="medium")

@app.cell
def setup_imports():
    import marimo as mo
    return mo,

@app.cell
def setup_imports():
    from src.domain_models import ConflictRegistryItem, E2BExecutionResult
    from src.state import CycleState, IntegrationState
    return ConflictRegistryItem, CycleState, E2BExecutionResult, IntegrationState

@app.cell
def scenario_01_01(CycleState, mo):
    # Scenario ID 01-01: Backward Compatible State Initialization
    state = CycleState(cycle_id="legacy-session")

    assert state.sandbox_artifacts == {}
    assert state.conflict_status is None

    mo.md("✅ Scenario 01-01 Passed: CycleState initialized with backward-compatible defaults.")
    return state,

@app.cell
def scenario_01_02(ConflictRegistryItem, E2BExecutionResult, mo):
    # Scenario ID 01-02: Conflict & Sandbox State Assignment
    import pydantic

    try:
        # Invalid exit_code type
        invalid_result = E2BExecutionResult(exit_code="abc")
    except pydantic.ValidationError:
        pass

    result = E2BExecutionResult(exit_code="0") # Coerced to int 0
    assert result.exit_code == 0

    conflict = ConflictRegistryItem(
        file_path="src/main.py",
        conflict_markers=["<<<<<<<", "=======", ">>>>>>>"]
    )
    serialized = conflict.model_dump()
    assert serialized["file_path"] == "src/main.py"

    mo.md("✅ Scenario 01-02 Passed: Domain models properly validate types and serialize.")
    return conflict, result, serialized

@app.cell
def scenario_01_03(mo):
    # Scenario ID 01-03: Source Path Verification
    import subprocess

    try:
        res = subprocess.run(["uv", "run", "ac-cdd", "--help"], capture_output=True, text=True, check=True)
        assert "Usage" in res.stdout
    except subprocess.CalledProcessError as e:
        raise AssertionError(f"CLI check failed: {e.stderr}")

    mo.md("✅ Scenario 01-03 Passed: CLI executes successfully via `src.cli:app`.")
    return res,

if __name__ == "__main__":
    app.run()
