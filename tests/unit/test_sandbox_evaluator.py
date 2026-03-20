from typing import Any
from unittest.mock import AsyncMock

import pytest

from src.enums import FlowStatus
from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
from src.state import CycleState


@pytest.fixture
def mock_mcp_manager() -> Any:
    manager = AsyncMock()
    manager.__aenter__.return_value = manager
    manager.get_tools.return_value = []
    return manager

from unittest.mock import patch


@pytest.fixture
def mock_process_runner() -> Any:
    runner = AsyncMock()
    runner.run_command.return_value = ("", "", 0, False)
    return runner


@pytest.fixture
def base_state() -> CycleState:
    state = CycleState(cycle_id="01")
    state.sandbox_id = "test_sandbox_123"
    return state


@pytest.mark.asyncio
async def test_evaluate_mechanical_blockade_passes(
    base_state: CycleState, mock_mcp_manager: Any, mock_process_runner: Any
) -> None:
    mock_process_runner.run_command.return_value = ("Success output", "", 0, False)

    with patch("src.nodes.sandbox_evaluator.ChatOpenAI") as mock_chat:
        mock_instance = MagicMock()
        mock_instance.bind_tools.return_value = MagicMock()
        mock_chat.return_value = mock_instance
        node = SandboxEvaluatorNodes(mcp_manager=mock_mcp_manager, process_runner=mock_process_runner)

        result = await node.sandbox_evaluate_node(base_state)

    assert result["status"] == FlowStatus.READY_FOR_AUDIT
    assert "structural_report" in result


@pytest.mark.asyncio
async def test_evaluate_mechanical_blockade_fails(
    base_state: CycleState, mock_mcp_manager: Any, mock_process_runner: Any
) -> None:
    def side_effect(cmd, **kwargs):
        if "test" in " ".join(cmd):
            return ("", "Test failed", 1, False)
        return ("", "", 0, False)

    mock_process_runner.run_command.side_effect = side_effect

    with patch("src.nodes.sandbox_evaluator.ChatOpenAI") as mock_chat:
        mock_instance = MagicMock()
        mock_instance.bind_tools.return_value = MagicMock()
        mock_chat.return_value = mock_instance
        node = SandboxEvaluatorNodes(mcp_manager=mock_mcp_manager, process_runner=mock_process_runner)

        result = await node.sandbox_evaluate_node(base_state)

    assert result["status"] == FlowStatus.TDD_FAILED
    assert "Verification failed" in result["error"]
    assert "structural_report" in result
