import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.jules_client import JulesClient


class TestSessionStateValidation:
    """Validate session state checking before operations."""

    @pytest.fixture
    def mock_client(self):  # type: ignore[no-untyped-def]
        with (
            patch.dict(
                os.environ,
                {"OPENAI_API_KEY": "mock", "JULES_API_KEY": "mock", "E2B_API_KEY": "mock"},
            ),
            patch("src.config.Settings.validate_api_keys", return_value=None),
            patch(
                "src.services.jules_client.google.auth.default",
                return_value=(MagicMock(), "mock-project"),
            ),
            patch.object(JulesClient, "__init__", lambda x: None),
        ):
            client = JulesClient()
            client.base_url = "https://mock.api"
            client.api_client = MagicMock()
            client.credentials = MagicMock()
            client._get_headers = MagicMock(return_value={})  # type: ignore
            return client

    @pytest.mark.asyncio
    async def test_get_session_state_in_progress(self, mock_client) -> None:  # type: ignore[no-untyped-def]
        """Should return IN_PROGRESS for active session."""
        # Mock API response via httpx since _request might be lower level in api_client but JulesClient mostly uses it or httpx directly.
        # Looking at HANDOFF_SUMMARY implementation, get_session_state uses a fresh httpx client.
        # So we should mock httpx.AsyncClient.

        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"state": "IN_PROGRESS"}
            mock_instance.get.return_value = mock_response

            state = await mock_client.get_session_state("sessions/123")

            assert state == "IN_PROGRESS"
            # Verify URL normalization logic if implemented, or just the call
            # The method implementation should handle sessions/ prefix or not

    @pytest.mark.asyncio
    async def test_get_session_state_completed(self, mock_client) -> None:  # type: ignore[no-untyped-def]
        """Should return COMPLETED for finished session."""
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_instance

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"state": "COMPLETED"}
            mock_instance.get.return_value = mock_response

            state = await mock_client.get_session_state("sessions/123")

            assert state == "COMPLETED"

    @pytest.mark.asyncio
    async def test_get_session_state_on_error(self, mock_client) -> None:  # type: ignore[no-untyped-def]
        """Should return UNKNOWN on exception."""
        with patch("httpx.AsyncClient") as mock_cls:
            mock_instance = AsyncMock()
            mock_cls.return_value.__aenter__.return_value = mock_instance
            mock_instance.get.side_effect = Exception("Connection Error")

            state = await mock_client.get_session_state("sessions/123")

            assert state == "UNKNOWN"
