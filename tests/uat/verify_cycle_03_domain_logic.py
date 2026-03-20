import marimo

__generated_with = "0.10.14"
app = marimo.App(width="medium")


@app.cell
def _() -> tuple[()]:
    import asyncio
    import os
    from unittest.mock import AsyncMock

    # Setup environment for testing before any imports from src
    os.environ["JULES_API_KEY"] = "dummy"
    os.environ["E2B_API_KEY"] = "dummy"
    os.environ["OPENROUTER_API_KEY"] = "dummy"
    os.environ["TEST_MODE"] = "True"

    from src.domain_models.verification_schema import StructuralGateReport
    from src.enums import FlowStatus
    from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
    from src.process_runner import ProcessRunner
    from src.state import CycleState

    # Scenario 1: Static Analysis Blockade (Ruff/Mypy failures)
    print("--- Running Scenario 1: Static Analysis Blockade ---")  # noqa: T201

    # Mock ProcessRunner to simulate Ruff failure
    _mock_runner = AsyncMock(spec=ProcessRunner)
    _mock_runner.run_command.side_effect = [
        ("", "lint error: unused import", 1),  # Ruff fails
        ("ok", "", 0),  # Mypy passes
        ("ok", "", 0),  # Pytest passes
    ]

    _node = SandboxEvaluatorNodes(process_runner=_mock_runner)
    _state = CycleState(cycle_id="03_scenario1")

    _result = asyncio.run(_node.sandbox_evaluate_node(_state))

    assert _result["status"] == FlowStatus.TDD_FAILED
    _report = _result["structural_report"]
    assert isinstance(_report, StructuralGateReport)
    assert not _report.passed
    assert not _report.lint_result.passed

    print("Scenario 1 Passed: Mechanical gatekeeper blocked execution on linting failure.")  # noqa: T201
    return (SandboxEvaluatorNodes, ProcessRunner, CycleState, FlowStatus, StructuralGateReport, asyncio, AsyncMock)


@app.cell
def _(
    CycleState: type,
    FlowStatus: type,
    ProcessRunner: type,
    SandboxEvaluatorNodes: type,
    StructuralGateReport: type,
    asyncio: type,
    AsyncMock: type,
) -> tuple[()]:
    # Scenario 2: Dynamic Unit Test Blockade (Pytest failure)
    print("\n--- Running Scenario 2: Dynamic Unit Test Blockade ---")  # noqa: T201

    # Mock ProcessRunner to simulate Pytest failure
    _mock_runner2 = AsyncMock(spec=ProcessRunner)
    _mock_runner2.run_command.side_effect = [
        ("ok", "", 0),  # Ruff passes
        ("ok", "", 0),  # Mypy passes
        ("", "AssertionError: expected True but got False", 1),  # Pytest fails
    ]

    _node2 = SandboxEvaluatorNodes(process_runner=_mock_runner2)
    _state2 = CycleState(cycle_id="03_scenario2")

    _result2 = asyncio.run(_node2.sandbox_evaluate_node(_state2)) # type: ignore

    assert _result2["status"] == FlowStatus.TDD_FAILED
    _report2 = _result2["structural_report"]
    assert isinstance(_report2, StructuralGateReport)
    assert not _report2.passed
    assert not _report2.test_result.passed
    assert "AssertionError" in _result2["error"]

    print("Scenario 2 Passed: Mechanical gatekeeper blocked execution on unit test failure.")  # noqa: T201
    return ()


if __name__ == "__main__":
    app.run()
