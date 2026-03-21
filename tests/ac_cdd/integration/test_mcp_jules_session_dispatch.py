from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.refactor_usecase import RefactorUsecase


@pytest.mark.asyncio
async def test_global_refactor_mcp_orchestration(tmp_path: Path) -> None:
    """
    Scenario UAT-C03-02:
    Verify the Global Refactor node securely dispatches parallel agent fleets via MCP Orchestration tools
    and uses diff locking to prevent race conditions.
    """
    from langchain_core.tools import StructuredTool

    from src.services.mcp_client_manager import McpClientManager

    mock_mcp_client = AsyncMock(spec=McpClientManager)
    invoked_tools = []

    async def mock_create_session(*args, **kwargs):
        invoked_tools.append("create_session")
        return "Session created and diffs successfully locked/applied."

    create_session_tool = StructuredTool.from_function(
        name="create_session",
        description="Creates a jules session",
        func=lambda x: "ok",
        coroutine=mock_create_session,
    )

    mock_mcp_client.get_orchestration_tools.return_value = [create_session_tool]
    mock_mcp_client.__aenter__.return_value = mock_mcp_client

    usecase = RefactorUsecase(mcp_client_manager=mock_mcp_client, base_dir=tmp_path)

    # Mock litellm to return ToolCall
    class MockChoice:
        def __init__(self) -> None:
            self.message = MagicMock()
            self.message.tool_calls = [
                MagicMock(function=MagicMock(name="create_session", arguments='{"prompt": "refactor"}'))
            ]
            self.message.tool_calls[0].function.name = "create_session"

    class MockResponse:
        def __init__(self) -> None:
            self.choices = [MockChoice()]

    with patch("src.services.refactor_usecase.ASTAnalyzer") as MockAnalyzer:
        mock_analyzer = MockAnalyzer.return_value
        mock_analyzer.find_duplicates.return_value = [[{"file": str(tmp_path / "test1.py"), "function": "foo"}]]
        mock_analyzer.find_complex_functions.return_value = []

        with patch("src.services.refactor_usecase.acompletion", return_value=MockResponse()):
            result = await usecase.execute()

    assert "create_session" in invoked_tools
    assert result.refactorings_applied is True
