from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, ToolCall

from src.services.integration_usecase import IntegrationUsecase
from src.state import IntegrationState


@pytest.fixture
def mock_git_env(tmp_path: Path) -> Path:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    return repo_dir


@pytest.mark.asyncio
async def test_master_integrator_mcp_git_writes(mock_git_env: Path) -> None:
    """
    Scenario UAT-C03-01:
    Verify the Master Integrator node securely pushes code and creates PRs via MCP Write tools.
    """
    from langchain_core.tools import StructuredTool

    from src.services.mcp_client_manager import McpClientManager

    mock_mcp_client = AsyncMock(spec=McpClientManager)

    # Track invocations
    invoked_tools = []

    async def mock_push_commit(*args, **kwargs):
        invoked_tools.append("push_commit")
        return "Commit successful."

    async def mock_create_pr(*args, **kwargs):
        invoked_tools.append("create_pull_request")
        return "https://github.com/test/repo/pull/123"

    push_tool = StructuredTool.from_function(
        name="push_commit",
        description="Pushes a commit",
        func=lambda x: "ok",
        coroutine=mock_push_commit,
    )
    pr_tool = StructuredTool.from_function(
        name="create_pull_request",
        description="Creates a PR",
        func=lambda x: "ok",
        coroutine=mock_create_pr,
    )

    mock_mcp_client.get_write_tools.return_value = [push_tool, pr_tool]
    mock_mcp_client.__aenter__.return_value = mock_mcp_client

    usecase = IntegrationUsecase(mcp_client_manager=mock_mcp_client)
    state = IntegrationState()

    # Mock litellm to return ToolCalls invoking both tools
    tool_calls = [
        ToolCall(
            name="push_commit",
            args={"message": "UAT-C03 test commit"},
            id="call_1",
            type="function"
        ),
        ToolCall(
            name="create_pull_request",
            args={"title": "UAT PR"},
            id="call_2",
            type="function"
        )
    ]

    _mock_msg = AIMessage(content="", tool_calls=tool_calls)

    # litellm expects standard openai format. So we map our ToolCall back into a format litellm returns
    class MockChoice:
        def __init__(self) -> None:
            self.message = MagicMock()
            self.message.tool_calls = [
                MagicMock(function=MagicMock(name="push_commit", arguments='{"message": "UAT test commit"}')),
                MagicMock(function=MagicMock(name="create_pull_request", arguments='{"title": "UAT PR"}'))
            ]
            self.message.tool_calls[0].function.name = "push_commit"
            self.message.tool_calls[1].function.name = "create_pull_request"

    class MockResponse:
        def __init__(self) -> None:
            self.choices = [MockChoice()]

    with patch("src.services.integration_usecase.acompletion", return_value=MockResponse()):
        _new_state = await usecase.run_integration_loop(state, mock_git_env)

    assert "push_commit" in invoked_tools
    assert "create_pull_request" in invoked_tools
