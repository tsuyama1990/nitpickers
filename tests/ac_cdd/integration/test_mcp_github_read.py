from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.tools import BaseTool

from src.nodes.architect import ArchitectNodes
from src.state import CycleState


class DummyGitHubTool(BaseTool):
    name: str = "get_file_content"
    description: str = "A dummy read tool"
    return_value: str = "File Content 123"

    def _run(self, file_path: str) -> str:
        if "not_found" in file_path:
            return "Error: File not found"
        return self.return_value

    async def _arun(self, file_path: str) -> str:
        if "not_found" in file_path:
            return "Error: File not found"
        return self.return_value

@pytest.mark.asyncio
async def test_architect_get_file_content() -> None:
    # Test that architect receives and passes github tools correctly down to JulesClient
    state = CycleState(cycle_id="01")

    tool = DummyGitHubTool()

    jules_mock = AsyncMock()
    # mock run_session since architect delegates to it
    jules_mock.run_session.return_value = {"status": "success", "session_name": "test_session", "pr_url": "http://github.com/pr/123"}
    # Because we're using getattr(self.jules, "execute_command", self.jules.run_session), we want to make sure execute_command doesn't exist on mock to fall back, or we mock it explicitly. Since the fallback logic checks for existence, AsyncMock auto-creates it. So let's mock execute_command too, just in case. Or delete it.
    del jules_mock.execute_command


    dummy_tools = [tool]

    node = ArchitectNodes(github_read_tools=dummy_tools)

    with patch("src.nodes.architect.ProjectManager") as _:
        result = await node.architect_session_node(state)

    assert result["status"] == "architect_completed"

    # Assert tools were passed down
    jules_mock.run_session.assert_called_once()
    _called_args, called_kwargs = jules_mock.run_session.call_args
    assert "tools" in called_kwargs
    assert len(called_kwargs["tools"]) == 1
    assert called_kwargs["tools"][0].name == "get_file_content"


@pytest.mark.asyncio
async def test_mcp_github_read_fallback() -> None:
    # This verifies the agent behaves properly or captures the "file not found" string gracefully
    state = CycleState(cycle_id="01")
    tool = DummyGitHubTool()

    jules_mock = AsyncMock()
    del jules_mock.execute_command
    jules_mock.run_session.return_value = {"status": "success", "session_name": "test_session_fallback", "pr_url": "http://github.com/pr/124"}


    node = ArchitectNodes(github_read_tools=[tool])
    with patch("src.nodes.architect.ProjectManager") as _:
        result = await node.architect_session_node(state)

    assert result["status"] == "architect_completed"
    assert result["pr_url"] == "http://github.com/pr/124"
    assert "tools" in jules_mock.run_session.call_args[1]
