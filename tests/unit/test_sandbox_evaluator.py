from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.enums import FlowStatus
from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
from src.state import CycleState


@pytest.fixture
def mock_process_runner() -> Any:
    runner = AsyncMock()
    runner.run_command.return_value = ("Success", "", 0, False)
    return runner


@pytest.fixture
def base_state() -> CycleState:
    state = CycleState(cycle_id="01")
    state.sandbox_id = "test_sandbox_123"
    return state


@pytest.mark.asyncio
async def test_evaluate_success_passes(base_state: CycleState, mock_process_runner: Any) -> None:
    node = SandboxEvaluatorNodes(process_runner=mock_process_runner)
    result = await node.sandbox_evaluate_node(base_state)

    assert result["status"] == FlowStatus.READY_FOR_AUDIT
    assert result["error"] is None
    assert "structural_report" in result
    report = result["structural_report"]
    assert report.passed


@pytest.mark.asyncio
async def test_evaluate_failure_fails(base_state: CycleState, mock_process_runner: Any) -> None:
    mock_process_runner.run_command.side_effect = [
        ("Success", "", 0, False),  # lint
        ("Success", "", 0, False),  # type
        ("", "Test failed", 1, False),  # test
    ]

    node = SandboxEvaluatorNodes(process_runner=mock_process_runner)
    result = await node.sandbox_evaluate_node(base_state)

    assert result["status"] == FlowStatus.TDD_FAILED
    assert "Verification failed" in result["error"]
    assert "structural_report" in result
    report = result["structural_report"]
    assert not report.passed
