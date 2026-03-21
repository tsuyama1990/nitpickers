import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.mcp_router.manager import McpClientManager
from src.mcp_router.schemas import E2bMcpConfig


def test_e2b_config_validation() -> None:
    # Test that E2bMcpConfig raises an error if E2B_API_KEY is missing
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValidationError) as exc:
            E2bMcpConfig()  # type: ignore[call-arg]
        assert "E2B_API_KEY" in str(exc.value)


def test_e2b_config_success() -> None:
    # Test valid configuration
    with patch.dict(os.environ, {"E2B_API_KEY": "e2b_valid_key123"}):
        config = E2bMcpConfig()  # type: ignore[call-arg]
        params = config.get_connection_config()
        e2b = params["e2b"]
        assert e2b["command"] == "npx"
        assert e2b["args"] == ["-y", "@e2b/mcp-server"]
        assert e2b["env"] is not None
        assert e2b["env"]["E2B_API_KEY"] == "e2b_valid_key123"


def test_mcp_client_manager_sanitization() -> None:
    # Test that SUDO_* environment variables are stripped out
    test_env = {
        "NORMAL_VAR": "value",
        "SUDO_COMMAND": "secret_injection",
        "SUDO_USER": "root"
    }

    with patch.dict(os.environ, test_env, clear=True):
        manager = McpClientManager()
        sanitized = manager._sanitize_environment()

        assert "NORMAL_VAR" in sanitized
        assert "SUDO_COMMAND" not in sanitized
        assert "SUDO_USER" not in sanitized


@pytest.mark.asyncio
async def test_mcp_client_manager_context() -> None:
    # Test that the context manager yields a client with correct parameters
    with patch.dict(os.environ, {"E2B_API_KEY": "e2b_test_key123", "SUDO_CMD": "secret"}):
        manager = McpClientManager()

        # We mock the MultiServerMCPClient to avoid actually starting node processes
        with patch("src.mcp_router.manager.MultiServerMCPClient") as mock_client_cls:
            async with manager.get_client() as _client:
                mock_client_cls.assert_called_once()

                # Check that the client was initialized with the sanitized environment configuration
                call_args = mock_client_cls.call_args[0][0]
                assert "e2b" in call_args

                e2b_config = call_args["e2b"]
                assert e2b_config["command"] == "npx"
                assert "SUDO_CMD" not in e2b_config["env"]
                assert e2b_config["env"]["E2B_API_KEY"] == "e2b_test_key123"
