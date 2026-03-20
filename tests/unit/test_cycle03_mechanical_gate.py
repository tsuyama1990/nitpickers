from unittest.mock import AsyncMock

import pytest

from src.domain_models.verification_schema import StructuralGateReport, VerificationResult
from src.enums import FlowStatus
from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
from src.process_runner import ProcessRunner
from src.state import CycleState


def test_verification_result_passed_property() -> None:
    pass_res = VerificationResult(command="test", exit_code=0, stdout="ok", stderr="")
    fail_res = VerificationResult(command="test", exit_code=1, stdout="", stderr="err")

    assert pass_res.passed is True
    assert fail_res.passed is False


def test_structural_gate_report_passed_property() -> None:
    pass_res = VerificationResult(command="test", exit_code=0, stdout="ok", stderr="")
    fail_res = VerificationResult(command="test", exit_code=1, stdout="", stderr="err")

    report_all_pass = StructuralGateReport(
        lint_result=pass_res,
        type_check_result=pass_res,
        test_result=pass_res,
    )
    assert report_all_pass.passed is True

    report_one_fail = StructuralGateReport(
        lint_result=pass_res,
        type_check_result=fail_res,
        test_result=pass_res,
    )
    assert report_one_fail.passed is False


def test_structural_gate_report_get_failure_report() -> None:
    pass_res = VerificationResult(command="pytest", exit_code=0, stdout="ok", stderr="")
    fail_lint = VerificationResult(command="ruff", exit_code=1, stdout="", stderr="lint error")
    fail_type = VerificationResult(
        command="mypy",
        exit_code=1,
        stdout="type error stdout",
        stderr="",  # Test stdout fallback
    )

    report = StructuralGateReport(
        lint_result=fail_lint,
        type_check_result=fail_type,
        test_result=pass_res,
    )

    failure_text = report.get_failure_report()
    assert "--- Linting Failed ---" in failure_text
    assert "Command: ruff" in failure_text
    assert "lint error" in failure_text
    assert "--- Type Checking Failed ---" in failure_text
    assert "type error stdout" in failure_text
    assert "--- Testing Failed ---" not in failure_text


@pytest.mark.asyncio
async def test_sandbox_evaluator_all_pass() -> None:
    mock_runner = AsyncMock(spec=ProcessRunner)
    mock_runner.run_command.return_value = ("ok", "", 0)

    node = SandboxEvaluatorNodes(process_runner=mock_runner)
    state = CycleState(cycle_id="01")

    result = await node.sandbox_evaluate_node(state)

    assert result["status"] == FlowStatus.READY_FOR_AUDIT
    assert "structural_report" in result
    report = result["structural_report"]
    assert isinstance(report, StructuralGateReport)
    assert report.passed is True


@pytest.mark.asyncio
async def test_sandbox_evaluator_lint_fails() -> None:
    mock_runner = AsyncMock(spec=ProcessRunner)

    # First call (lint) fails, others pass
    mock_runner.run_command.side_effect = [
        ("", "lint failed", 1),  # lint
        ("ok", "", 0),  # mypy
        ("ok", "", 0),  # pytest
    ]

    node = SandboxEvaluatorNodes(process_runner=mock_runner)
    state = CycleState(cycle_id="01")

    result = await node.sandbox_evaluate_node(state)

    assert result["status"] == FlowStatus.TDD_FAILED
    assert "Verification failed" in result["error"]
    assert "lint failed" in result["error"]

    report = result["structural_report"]
    assert report.passed is False
    assert report.lint_result.passed is False
    assert report.type_check_result.passed is True


@pytest.mark.asyncio
async def test_sandbox_evaluator_handles_exception() -> None:
    mock_runner = AsyncMock(spec=ProcessRunner)

    msg = "Simulated crash"
    mock_runner.run_command.side_effect = Exception(msg)

    node = SandboxEvaluatorNodes(process_runner=mock_runner)
    state = CycleState(cycle_id="01")

    result = await node.sandbox_evaluate_node(state)

    assert result["status"] == FlowStatus.TDD_FAILED
    assert msg in result["error"]
