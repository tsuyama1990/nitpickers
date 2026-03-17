from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from ac_cdd_core.domain_models import ArchitectCriticResponse
from ac_cdd_core.enums import FlowStatus
from ac_cdd_core.graph_nodes import CycleNodes
from ac_cdd_core.sandbox import SandboxRunner
from ac_cdd_core.services.jules_client import JulesClient
from ac_cdd_core.state import CycleState


@pytest.fixture
def mock_jules_client() -> Any:
    client = AsyncMock(spec=JulesClient)
    client._get_session_url.return_value = "http://mock.session.url"
    return client

@pytest.fixture
def cycle_nodes(mock_jules_client) -> Any:  # type: ignore
    sandbox = AsyncMock(spec=SandboxRunner)
    return CycleNodes(sandbox_runner=sandbox, jules_client=mock_jules_client)

@pytest.mark.asyncio
async def test_architect_critic_node_rejected(cycle_nodes, mock_jules_client) -> Any:  # type: ignore
    state = CycleState(
        cycle_id="test-cycle",
        jules_session_name="test-session",
        critic_feedback=[],
        is_architecture_locked=False,
    )

    # Mock Litellm or JulesClient returning a failed response
    mock_response = ArchitectCriticResponse(
        is_passed=False,
        feedback=["N+1 query problem detected", "Missing User Interface contract"]
    )

    with patch("ac_cdd_core.graph_nodes.settings") as mock_settings:
        mock_settings.get_template.return_value.read_text.return_value = "Mock Instruction"
        with patch("ac_cdd_core.graph_nodes.get_model"):
            # We mock the internal agent call inside architect_critic_node
            agent_mock = AsyncMock()
            agent_mock.run.return_value.data = mock_response
            with patch("ac_cdd_core.graph_nodes.Agent", return_value=agent_mock):
                result = await cycle_nodes.architect_critic_node(state)

    assert result["status"] == FlowStatus.CRITIC_REJECTED.value
    assert result["is_architecture_locked"] is False
    assert len(result["critic_feedback"]) == 2
    assert "N+1 query problem detected" in result["critic_feedback"]


@pytest.mark.asyncio
async def test_architect_critic_node_approved(cycle_nodes, mock_jules_client) -> Any:  # type: ignore
    state = CycleState(
        cycle_id="test-cycle",
        jules_session_name="test-session",
        critic_feedback=[],
        is_architecture_locked=False,
    )

    # Mock Litellm or JulesClient returning an approved response
    mock_response = ArchitectCriticResponse(
        is_passed=True,
        feedback=[]
    )

    with patch("ac_cdd_core.graph_nodes.settings") as mock_settings:
        mock_settings.get_template.return_value.read_text.return_value = "Mock Instruction"
        with patch("ac_cdd_core.graph_nodes.get_model"):
            agent_mock = AsyncMock()
            agent_mock.run.return_value.data = mock_response
            with patch("ac_cdd_core.graph_nodes.Agent", return_value=agent_mock):
                result = await cycle_nodes.architect_critic_node(state)

    assert result["status"] == FlowStatus.ARCHITECTURE_APPROVED.value
    assert result["is_architecture_locked"] is True
    assert len(result["critic_feedback"]) == 0
