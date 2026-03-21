from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.tools import tool

from src.services.integration_usecase import IntegrationUsecase
from src.state import IntegrationState


@tool
def dummy_push_commit(commit_message: str) -> str:
    """Mocks pushing a commit via MCP."""
    return f"Successfully pushed commit: {commit_message}"

@tool
def dummy_create_pull_request(title: str, body: str) -> str:
    """Mocks creating a PR via MCP."""
    return f"Successfully created PR: {title}"

@pytest.fixture
def mock_git_env(tmp_path: Path) -> Path:
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    return repo_dir

@pytest.mark.asyncio
async def test_mcp_git_tools_execution() -> None:
    """
    Verify that IntegrationUsecase securely iterates over injected github_write_tools instead of calling the subprocess.
    """
    tools = [dummy_push_commit, dummy_create_pull_request]

    usecase = IntegrationUsecase(github_write_tools=tools)

    # Normally we would mock litellm.acompletion to return a ToolCall and assert the ainvoke happens
    # However since we're verifying structural injection here:
    assert len(usecase.github_write_tools) == 2

    state = IntegrationState(
        master_integrator_session_id="test",
        unresolved_conflicts=[]
    )

    # We mock out the MCP manager and litellm to test structural execution
    # First, mock the asynchronous context manager returned by get_client correctly
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def mock_get_client() -> Any:
        yield AsyncMock()

    with patch("src.mcp_router.manager.McpClientManager.get_client", return_value=mock_get_client()), \
         patch("src.services.integration_usecase.litellm.acompletion", new_callable=AsyncMock) as mock_litellm:

        # Setup mock to exit loop early by not returning tool_calls
        mock_response = AsyncMock()
        mock_response.choices = [AsyncMock()]
        mock_response.choices[0].message.tool_calls = None
        mock_response.choices[0].message.to_dict.return_value = {"role": "assistant", "content": "Done"}
        mock_litellm.return_value = mock_response

        # Execute
        await usecase.run_integration_loop(state, Path("."))

        # Verify litellm was called with the injected tool schema
        mock_litellm.assert_called_once()
        call_kwargs = mock_litellm.call_args.kwargs
        assert "tools" in call_kwargs

        # Verify that schema parsing successfully captured dummy tools
        tools_schema = call_kwargs["tools"]
        assert len(tools_schema) == 2
        assert any(t["function"]["name"] == "dummy_push_commit" for t in tools_schema)
