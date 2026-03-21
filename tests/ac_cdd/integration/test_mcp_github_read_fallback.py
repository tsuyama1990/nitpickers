from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.nodes.architect import ArchitectNodes
from src.state import CycleState


@pytest.mark.asyncio
async def test_mcp_github_read_fallback() -> None:
    # UAT 02-03: Graceful Error Handling and Recovery
    # Given the Architect node is initialized with GitHub tools bound

    mock_jules = MagicMock()
    mock_jules.git_context = AsyncMock()
    mock_jules.git_context.prepare_git_context = AsyncMock(return_value=("mockowner", "mockrepo", "mockbranch"))

    # Stub execute_command logic
    mock_jules.execute_command = AsyncMock(return_value={"status": "success", "session_name": "mock-sess", "pr_url": "http://pr/1"})

    mock_git = AsyncMock()
    mock_git.create_feature_branch = AsyncMock()
    mock_git.merge_pr = AsyncMock()

    node = ArchitectNodes(mock_jules, mock_git)

    # Mock litellm to call a tool, then stop
    call_counts = {"count": 0}
    async def mock_acompletion(*args: Any, **kwargs: Any) -> Any:
        call_counts["count"] += 1
        class MockChoice:
            def __init__(self, msg: Any) -> None:
                self.message = msg
        class MockResponse:
            def __init__(self, choices: Any) -> None:
                self.choices = choices

        if call_counts["count"] == 1:
            # Return a tool call
            class MockFunction:
                name = "github_get_file_content"
                arguments = '{"path": "non_existent_file.py"}'
            class MockToolCall:
                id = "call_123"
                function = MockFunction()
            class MockMessage:
                def __init__(self) -> None:
                    self.content = None
                    self.tool_calls = [MockToolCall()]
                def model_dump(self) -> dict[str, Any]:
                    return {"role": "assistant", "tool_calls": [{"id": "call_123", "type": "function", "function": {"name": "github_get_file_content", "arguments": '{"path": "non_existent_file.py"}'}}]}
            return MockResponse([MockChoice(MockMessage())])
        # Return DONE
        class MockMessageDone:
            content = "DONE"
            tool_calls = None
            def model_dump(self) -> dict[str, Any]:
                return {"role": "assistant", "content": "DONE"}
        return MockResponse([MockChoice(MockMessageDone())])

    # Mock tool
    class MockArgs(BaseModel):
        path: str = Field(...)

    async def mock_tool_arun(*args: Any, **kwargs: Any) -> str:
        return '{"jsonrpc": "2.0", "error": {"code": -32603, "message": "File not found"}}'

    def mock_tool_run(*args: Any, **kwargs: Any) -> str:
        return '{"jsonrpc": "2.0", "error": {"code": -32603, "message": "File not found"}}'

    tool = StructuredTool(
        name="github_get_file_content",
        description="mock tool",
        args_schema=MockArgs,
        func=mock_tool_run,
        coroutine=mock_tool_arun,
    )
    object.__setattr__(tool, "server_name", "github")

    with patch("litellm.acompletion", new=mock_acompletion), \
         patch("src.services.mcp_client_manager.McpClientManager.get_readonly_tools", new_callable=AsyncMock) as mock_get_tools:
        mock_get_tools.return_value = [tool]

        state = CycleState(cycle_id="01")

        # When the node autonomously invokes get_file_content requesting deliberately non-existent file
        result = await node.architect_session_node(state)

        # Then the GitHub MCP server returns standard JSON RPC error indicating File Not Found
        # AND the error is formatted and returned to LLM natively
        # AND the LangGraph execution does not crash

        assert result.get("status") == "architect_completed"

        # Verify the context was appended with the error
        mock_jules.execute_command.assert_called_once()
        call_kwargs = mock_jules.execute_command.call_args[1]

        assert "=== REPOSITORY CONTEXT ===" in call_kwargs["prompt"]
        assert "File not found" in call_kwargs["prompt"]
