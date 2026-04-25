import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.jules_session_nodes import JulesSessionNodes
from src.jules_session_state import JulesSessionState, SessionStatus
from src.services.git.checkout import GitCheckoutMixin


@pytest.mark.asyncio
async def test_monitor_session_failure_diagnostics() -> None:
    """Verify that monitor_session fetches activities when failure reason is missing from outputs."""
    # Setup
    mock_client = MagicMock()
    mock_client._get_headers.return_value = {}
    mock_client._sleep = AsyncMock()

    # Mock failure activity
    failure_reason = "Internal Bot Error: Resource Exhausted"
    mock_client.list_activities = AsyncMock(
        return_value=[{"name": "act-1", "sessionFailed": {"reason": failure_reason}}]
    )

    loop = asyncio.get_running_loop()
    start_time = loop.time()
    nodes = JulesSessionNodes(mock_client)
    state = JulesSessionState(session_url="http://test/session", start_time=start_time)

    with (
        patch("src.jules_session_nodes.httpx") as mock_httpx,
        patch("src.config.settings") as mock_settings,
    ):
        mock_settings.jules.monitor_batch_size = 1
        mock_settings.jules.monitor_poll_interval_seconds = 1
        mock_httpx.codes.OK = 200

        mock_instance = mock_httpx.AsyncClient.return_value
        mock_instance.__aenter__.return_value = mock_instance

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        # FAILED state but NO reason in outputs
        mock_resp.json.return_value = {"state": "FAILED", "outputs": []}
        mock_instance.get = AsyncMock(return_value=mock_resp)

        # Run
        new_state = await nodes.monitor_session(state)

        # Verify
        assert mock_client.list_activities.called
        assert failure_reason in new_state["error"]
        assert new_state["status"] == SessionStatus.FAILED


@pytest.mark.asyncio
async def test_git_checkout_resilience() -> None:
    """Verify that _auto_commit_if_dirty handles conflicts by attempting aborts."""
    mock_runner = AsyncMock()
    # Simulate conflict state: UU code in git status
    mock_runner.run_command.side_effect = [
        ("UU conflicted_file.py\n", "", 0, ""),  # git status --porcelain
        ("", "", 0, ""),  # git status after aborts (now clean for simplicity)
    ]

    manager = GitCheckoutMixin()
    manager.runner = mock_runner
    # manager._run_git = AsyncMock()  # This triggers method-assign error
    with (
        patch.object(manager, "_run_git", new_callable=AsyncMock) as mock_run_git,
        patch("src.config.settings") as mock_settings,
    ):
        mock_settings.tools.conflict_codes = ["UU", "AA"]

        # Run
        await manager._auto_commit_if_dirty("test commit")

        # Verify abort attempts were called
        abort_calls = [call.args[0] for call in mock_run_git.call_args_list]
        assert ["rebase", "--abort"] in abort_calls
        assert ["merge", "--abort"] in abort_calls

        # Verify it didn't raise RuntimeError if second status check was clean
        # (In this mock it's empty, so it just returns)


@pytest.mark.asyncio
async def test_monitor_session_recovery_nudge() -> None:
    """Verify that monitor_session sends a recovery nudge on FAILED state."""
    # Setup
    mock_client = MagicMock()
    mock_client._get_headers.return_value = {}
    mock_client._send_message = AsyncMock()
    mock_client._sleep = AsyncMock()
    mock_client.list_activities = AsyncMock(return_value=[])

    loop = asyncio.get_running_loop()
    start_time = loop.time()
    nodes = JulesSessionNodes(mock_client)
    state = JulesSessionState(session_url="http://test/session", start_time=start_time)

    with (
        patch("src.jules_session_nodes.httpx") as mock_httpx,
        patch("src.config.settings") as mock_settings,
    ):
        mock_settings.jules.monitor_batch_size = 2
        mock_settings.jules.monitor_poll_interval_seconds = 1
        mock_httpx.codes.OK = 200

        mock_instance = mock_httpx.AsyncClient.return_value
        mock_instance.__aenter__.return_value = mock_instance

        # 1st poll: FAILED
        # 2nd poll: STILL FAILED (now should actually fail)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"state": "FAILED", "outputs": []}
        mock_instance.get = AsyncMock(return_value=mock_resp)

        # Run
        new_state = await nodes.monitor_session(state)

        # Verify
        assert mock_client._send_message.called
        assert "recovery nudge" in mock_client._send_message.call_args[0][1]
        assert state.recovery_nudge_sent is True
        assert new_state["status"] == SessionStatus.FAILED  # Actually failed on 2nd poll
