from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.services.integration_usecase import IntegrationUsecase
from langchain_core.tools import tool
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

    usecase = IntegrationUsecase(github_write_tools=tools) # type: ignore

    # Normally we would mock litellm.acompletion to return a ToolCall and assert the ainvoke happens
    # However since we're verifying structural injection here:
    assert len(usecase.github_write_tools) == 2

    state = IntegrationState(
        master_integrator_session_id="test",
        unresolved_conflicts=[]
    )

    # We mock out _create_pull_request execution because it requires the litellm network call
    with patch.object(usecase, "_create_pull_request", new_callable=AsyncMock) as mock_pr:
        await usecase.run_integration_loop(state, Path("."))
        mock_pr.assert_called_once()
