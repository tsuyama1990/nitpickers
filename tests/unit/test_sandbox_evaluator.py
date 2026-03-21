from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.enums import FlowStatus
from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
from src.state import CycleState


class MockTool:
    def __init__(self, return_value: str) -> None:
        self.name = "execute_command"
        self.return_value = return_value
        self.ainvoke = AsyncMock(return_value=return_value)

@pytest.fixture
def mock_success_tool() -> Any:
    return [MockTool("Test passed")]

@pytest.fixture
def mock_fail_tool() -> Any:
    return [MockTool("Error: Test failed")]

@pytest.fixture
def base_state() -> CycleState:
    state = CycleState(cycle_id="01")
    return state

@pytest.mark.asyncio
async def test_evaluate_success_passes(
    base_state: CycleState, mock_success_tool: Any
) -> None:
    node = SandboxEvaluatorNodes(e2b_tools=mock_success_tool)
    result = await node.sandbox_evaluate_node(base_state)

    assert result["status"] == FlowStatus.READY_FOR_AUDIT

@pytest.mark.asyncio
async def test_evaluate_failure_fails(
    base_state: CycleState, mock_fail_tool: Any
) -> None:
    node = SandboxEvaluatorNodes(e2b_tools=mock_fail_tool)
    result = await node.sandbox_evaluate_node(base_state)

    assert result["status"] == FlowStatus.TDD_FAILED
    assert "Error: Test failed" in result["error"]
