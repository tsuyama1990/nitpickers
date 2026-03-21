from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.domain_models.execution import E2BExecutionResult
from src.enums import FlowStatus
from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
from src.state import CycleState


@pytest.fixture
def mock_executor() -> Any:
    executor = AsyncMock()
    executor.run_tests.return_value = E2BExecutionResult(
        stdout="Test passed", stderr="", exit_code=0
    )
    return executor


@pytest.fixture
def base_state() -> CycleState:
    state = CycleState(cycle_id="01")
    state.sandbox_id = "test_sandbox_123"
    return state


@pytest.mark.asyncio
async def test_evaluate_red_phase_success_fails(base_state: CycleState, mock_executor: Any) -> None:
    base_state.tdd_phase = "red"
    mock_executor.run_tests.return_value = E2BExecutionResult(
        stdout="Test passed", stderr="", exit_code=0
    )

    node = SandboxEvaluatorNodes(mcp_client=mock_executor)
    result = await node.sandbox_evaluate_node(base_state)

    assert result["status"] == FlowStatus.UAT_FAILED
    assert "immediately" in result["error"].lower()
    assert result["tdd_phase"] == "red"


@pytest.mark.asyncio
async def test_evaluate_red_phase_failure_passes(
    base_state: CycleState, mock_executor: Any
) -> None:
    base_state.tdd_phase = "red"
    mock_executor.run_tests.return_value = E2BExecutionResult(
        stdout="", stderr="Test failed", exit_code=1
    )

    node = SandboxEvaluatorNodes(mcp_client=mock_executor)
    result = await node.sandbox_evaluate_node(base_state)

    assert result["status"] == FlowStatus.READY_FOR_AUDIT
    assert result["tdd_phase"] == "green"


@pytest.mark.asyncio
async def test_evaluate_green_phase_success_passes(
    base_state: CycleState, mock_executor: Any
) -> None:
    base_state.tdd_phase = "green"
    mock_executor.run_tests.return_value = E2BExecutionResult(
        stdout="Test passed", stderr="", exit_code=0
    )

    node = SandboxEvaluatorNodes(mcp_client=mock_executor)
    result = await node.sandbox_evaluate_node(base_state)

    assert result["status"] == FlowStatus.READY_FOR_AUDIT
    assert result["tdd_phase"] == "green"


@pytest.mark.asyncio
async def test_evaluate_green_phase_failure_fails(
    base_state: CycleState, mock_executor: Any
) -> None:
    base_state.tdd_phase = "green"
    mock_executor.run_tests.return_value = E2BExecutionResult(
        stdout="", stderr="Test failed", exit_code=1
    )

    node = SandboxEvaluatorNodes(mcp_client=mock_executor)
    result = await node.sandbox_evaluate_node(base_state)

    assert result["status"] == FlowStatus.UAT_FAILED
    assert "Test failed" in result["error"]
    assert result["tdd_phase"] == "green"
