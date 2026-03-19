import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.jules_session_nodes import JulesSessionNodes, SessionStatus
from src.jules_session_state import JulesSessionState

async def run_test():
    mock_client = MagicMock()
    mock_client._get_headers.return_value = {}
    mock_client._sleep = AsyncMock()
    mock_client.inquiry_handler = MagicMock()
    mock_client.inquiry_handler.handle_plan_approval = AsyncMock()
    mock_client.inquiry_handler.check_for_inquiry = AsyncMock(return_value=None)
    mock_client._handle_manual_input = AsyncMock()

    loop = asyncio.get_running_loop()
    start_time = loop.time()
    nodes = JulesSessionNodes(mock_client)
    state = JulesSessionState(session_url="http://test/session", start_time=start_time)

    # Force IN_PROGRESS
    state.jules_state = None

    with patch("src.jules_session_nodes.httpx") as mock_httpx:
        with patch("src.config.settings") as mock_settings:
            mock_settings.jules.monitor_batch_size = 12
            mock_settings.jules.monitor_poll_interval_seconds = 5
            mock_settings.jules.stale_session_timeout_seconds = 3600
            mock_settings.jules.max_stale_nudges = 3

            mock_httpx.codes.OK = 200

            mock_instance = mock_httpx.AsyncClient.return_value
            mock_instance.__aenter__.return_value = mock_instance

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"state": "IN_PROGRESS", "outputs": []}

            mock_instance.get = AsyncMock(return_value=mock_resp)

            new_state = await nodes.monitor_session(state)
            print("Call count:", mock_instance.get.call_count)

asyncio.run(run_test())
