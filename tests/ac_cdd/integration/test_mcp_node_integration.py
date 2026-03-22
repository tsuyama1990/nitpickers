from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.tools import BaseTool

from src.enums import FlowStatus
from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
from src.state import CycleState


class DummyE2bTool(BaseTool):
    name: str = "execute_command"
    description: str = "A dummy tool"
    return_value: str = "Success"

    def _run(self, command: str) -> str:
        return self.return_value

    async def _arun(self, command: str) -> str:
        return self.return_value


@pytest.mark.asyncio
async def test_sandbox_evaluator_tool_binding() -> None:
    # Simulates ensuring the LLM or tool executor works with e2b tools correctly
    state = CycleState(cycle_id="01")

    # We provide a mock tool that simulates a successful run_code/execute_command tool
    tool = DummyE2bTool()

    # We must patch asyncio.wait_for because SandboxEvaluator executes tools with a timeout wrapper
    with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait_for:
        mock_wait_for.return_value = "Success"
        dummy_tools = [tool]

        node = SandboxEvaluatorNodes(e2b_tools=dummy_tools)
        result = await node.sandbox_evaluate_node(state)

        # It should correctly invoke the dummy tool internally
        assert result["status"] == FlowStatus.READY_FOR_AUDIT
        # ensure wait_for was called for lint, type check, test
        assert mock_wait_for.call_count == 3


@pytest.mark.asyncio
async def test_mcp_e2b_error_handling() -> None:
    # Simulates a stderr failure returning from the node script / dummy tool
    state = CycleState(cycle_id="01")

    tool = DummyE2bTool()
    with patch("asyncio.wait_for", new_callable=AsyncMock) as mock_wait_for:
        mock_wait_for.return_value = "Error: Command failed with exit code: 1"
        dummy_tools = [tool]

        node = SandboxEvaluatorNodes(e2b_tools=dummy_tools)
        result = await node.sandbox_evaluate_node(state)

        # Ensure failure is categorized properly and mapped without crashing
        assert result["status"] == FlowStatus.TDD_FAILED
        assert "Error: Command failed" in result["error"]
