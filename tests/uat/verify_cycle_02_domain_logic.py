from unittest.mock import AsyncMock, MagicMock

import pytest

from src.nodes.architect_critic import ArchitectCriticNodes
from src.state import CycleState


@pytest.fixture
def mock_jules() -> MagicMock:
    jules = MagicMock()
    jules._get_session_url.return_value = "https://mock.url/sessions/123"
    jules._send_message = AsyncMock()
    jules.wait_for_completion = AsyncMock()
    return jules


@pytest.mark.asyncio
async def test_uat_02_01_successful_critic_evaluation_loop(mock_jules: MagicMock) -> None:
    # UAT 02-01: Successful Critic Evaluation Loop
    state = CycleState(cycle_id="01")
    state.project_session_id = "session-123"

    mock_jules.wait_for_completion.return_value = {
        "status": "success",
        "raw": {"outputs": [{"text": '{"is_approved": true}'}]},
    }

    node = ArchitectCriticNodes()
    result = await node.architect_critic_node(state)

    assert result["status"] == "architect_completed"


@pytest.mark.asyncio
async def test_uat_02_02_vulnerable_spec_regeneration(mock_jules: MagicMock) -> None:
    # UAT 02-02: Vulnerable Spec Regeneration
    state = CycleState(cycle_id="01")
    state.project_session_id = "session-123"
    state.critic_retry_count = 0

    # Mock evaluate response rejection
    mock_jules.wait_for_completion.return_value = {
        "status": "success",
        "raw": {
            "outputs": [
                {"text": '{"is_approved": false, "vulnerabilities": ["Missing DB constraint"]}'}
            ]
        },
    }

    node = ArchitectCriticNodes()
    result = await node.architect_critic_node(state)

    assert result["status"] == "architect_critic_rejected"
    assert result["critic_retry_count"] == 1


@pytest.mark.asyncio
async def test_uat_02_03_critic_max_retries_limit(mock_jules: MagicMock) -> None:
    # UAT 02-03: Critic Max Retries Limit
    state = CycleState(cycle_id="01")
    state.project_session_id = "session-123"
    state.critic_retry_count = 2

    mock_jules.wait_for_completion.return_value = {
        "status": "success",
        "raw": {
            "outputs": [{"text": '{"is_approved": false, "vulnerabilities": ["Still failing"]}'}]
        },
    }

    node = ArchitectCriticNodes()
    result = await node.architect_critic_node(state)

    # Should forcefully fail or complete
    assert result["status"] == "architect_failed"
    assert result["critic_retry_count"] == 3
