import os
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.mcp_router.manager import McpClientManager
from src.mcp_router.schemas import E2bMcpConfig, GitHubMcpConfig
from src.mcp_router.tools import get_github_read_tools


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
    # Test that implicitly safe keys are kept while secrets are dropped based on blacklisting.
    test_env = {
        "PATH": "/usr/bin:/bin",
        "NORMAL_VAR": "value",
        "SUDO_COMMAND": "secret_injection",
        "SUDO_USER": "root",
        "API_KEY": "some_key",
        "GITHUB_TOKEN": "some_token"
    }

    with patch.dict(os.environ, test_env, clear=True):
        manager = McpClientManager()
        sanitized = manager._sanitize_environment()

        assert "PATH" in sanitized
        assert "NORMAL_VAR" in sanitized
        assert "SUDO_COMMAND" not in sanitized
        assert "SUDO_USER" not in sanitized
        assert "API_KEY" not in sanitized
        assert "GITHUB_TOKEN" not in sanitized


@pytest.mark.asyncio
async def test_mcp_client_manager_context() -> None:
    # Test that the context manager yields a client with correct parameters
    with patch.dict(os.environ, {"E2B_API_KEY": "e2b_test_key123", "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_mock_token_1234567890", "SUDO_CMD": "secret"}):
        manager = McpClientManager()

        # We mock the MultiServerMCPClient to avoid actually starting node processes
        with patch("src.mcp_router.manager.MultiServerMCPClient") as mock_client_cls:
            async with manager.get_client() as _client:
                mock_client_cls.assert_called_once()

                # Check that the client was initialized with the sanitized environment configuration
                call_args = mock_client_cls.call_args[0][0]
                assert "e2b" in call_args
                assert "github" in call_args

                e2b_config = call_args["e2b"]
                assert e2b_config["command"] == "npx"
                assert "SUDO_CMD" not in e2b_config["env"]
                assert e2b_config["env"]["E2B_API_KEY"] == "e2b_test_key123"

                github_config = call_args["github"]
                assert github_config["command"] == "npx"
                assert github_config["args"] == ["-y", "@modelcontextprotocol/server-github"]
                assert github_config["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "ghp_mock_token_1234567890"

def test_github_config_validation() -> None:
    # Test that GitHubMcpConfig raises an error if GITHUB_PERSONAL_ACCESS_TOKEN is missing
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValidationError) as exc:
            GitHubMcpConfig()  # type: ignore[call-arg]
        assert "GITHUB_PERSONAL_ACCESS_TOKEN" in str(exc.value)

def test_github_config_success() -> None:
    with patch.dict(os.environ, {"GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_mock_token_1234567890"}):
        config = GitHubMcpConfig()  # type: ignore[call-arg]
        params = config.get_connection_config()
        assert "github" in params
        assert params["github"]["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "ghp_mock_token_1234567890"

@pytest.mark.asyncio
async def test_get_github_read_tools_filtering() -> None:
    class MockTool:
        def __init__(self, name: str, server_name: str) -> None:
            self.name = name
            self.server_name = server_name

    class MockClient:
        async def get_tools(self) -> list[MockTool]:
            return [
                MockTool(name="get_file_content", server_name="github"),
                MockTool(name="push_commit", server_name="github"),
                MockTool(name="execute_command", server_name="e2b"),
            ]

    class MockContextManager:
        async def __aenter__(self) -> MockClient:
            return MockClient()
        async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            pass

    with patch.object(McpClientManager, "get_client", return_value=MockContextManager()):
        tools = await get_github_read_tools()
        assert len(tools) == 1
        assert tools[0].name == "get_file_content"
        assert getattr(tools[0], "server_name", "") == "github"
