from unittest.mock import AsyncMock, patch

import pytest
from ac_cdd_core.graph_nodes import CycleNodes
from ac_cdd_core.sandbox import SandboxRunner
from ac_cdd_core.services.jules_client import JulesClient
from ac_cdd_core.state import CycleState

@pytest.mark.asyncio
class TestArchitectCriticNode:
    @patch("ac_cdd_core.graph_nodes.GitManager")
    @patch("ac_cdd_core.graph_nodes.ProjectManager")
    async def test_critic_rejects(self, mock_pm: AsyncMock, mock_git: AsyncMock) -> None:
        sandbox = AsyncMock(spec=SandboxRunner)
        jules = AsyncMock(spec=JulesClient)
        nodes = CycleNodes(sandbox, jules)

        state = CycleState(cycle_id="1", jules_session_name="test_sess")

        # Mock the wait_for_completion and list_activities
        jules.wait_for_completion.return_value = {"pr_url": "http://pr/1"}
        jules.list_activities.return_value = [
            {"activity_type": "message", "author": "agent", "content": '```json\n{"status": "fail", "feedback": ["issue 1"]}\n```'}
        ]

        result = await nodes.architect_critic_node(state)

        assert result["status"] == "critic_rejected"
        assert result["critic_feedback"] == ["issue 1"]
        assert result["is_architecture_locked"] is False

    @patch("ac_cdd_core.graph_nodes.GitManager")
    @patch("ac_cdd_core.graph_nodes.ProjectManager")
    async def test_critic_approves(self, mock_pm: AsyncMock, mock_git: AsyncMock) -> None:
        sandbox = AsyncMock(spec=SandboxRunner)
        jules = AsyncMock(spec=JulesClient)
        nodes = CycleNodes(sandbox, jules)

        state = CycleState(cycle_id="1", jules_session_name="test_sess", integration_branch="main")

        # Mock the wait_for_completion and list_activities
        jules.wait_for_completion.return_value = {"pr_url": "http://pr/1"}
        jules.list_activities.return_value = [
            {"activity_type": "message", "author": "agent", "content": '```json\n{"status": "pass", "feedback": []}\n```'}
        ]

        result = await nodes.architect_critic_node(state)

        assert result["status"] == "architecture_approved"
        assert result["is_architecture_locked"] is True
        assert result["pr_url"] == "http://pr/1"
