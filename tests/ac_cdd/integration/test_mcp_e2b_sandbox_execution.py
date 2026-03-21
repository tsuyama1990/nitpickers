from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.tools import tool

from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
from src.state import CycleState


@pytest.fixture
def base_state() -> CycleState:
    state = CycleState(cycle_id="01")
    state.tdd_phase = "red"
    return state

@pytest.mark.asyncio
async def test_mcp_e2b_sandbox_execution(base_state):
    node = SandboxEvaluatorNodes()

    with patch("src.nodes.sandbox_evaluator.McpClientManager") as mock_mcp:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        node.mcp_client = mock_client

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_acompletion:
            # First return: LLM calls run_code tool
            tool_call_mock = AsyncMock()
            tool_call_mock.function.name = "run_code"
            tool_call_mock.function.arguments = '{"code": "print(1/0)"}'
            tool_call_mock.id = "call_123"

            message_mock = AsyncMock()
            message_mock.tool_calls = [tool_call_mock]

            choice_mock = AsyncMock()
            choice_mock.message = message_mock

            mock_acompletion.return_value.choices = [choice_mock]

            @tool
            def run_code(code: str) -> str:
                '''Execute code'''
                return "ZeroDivisionError: division by zero"

            mock_client.get_tools.return_value = [run_code]

            result = await node.sandbox_evaluate_node(base_state)

            assert result["status"] == "tdd_failed"
            assert "ZeroDivisionError" in result["error"]
