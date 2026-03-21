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
            E2bMcpConfig(_env_file=None, E2B_API_KEY="")  # type: ignore[call-arg]
        assert "E2B_API_KEY" in str(exc.value)


def test_github_config_validation() -> None:
    # Test that GitHubMcpConfig raises an error if GITHUB_PERSONAL_ACCESS_TOKEN is missing
    with patch.dict(os.environ, clear=True):
        with pytest.raises(ValidationError) as exc:
            GitHubMcpConfig(_env_file=None, GITHUB_PERSONAL_ACCESS_TOKEN="")  # type: ignore[call-arg]
        assert "GITHUB_PERSONAL_ACCESS_TOKEN" in str(exc.value)


def test_github_config_success() -> None:
    # Test valid configuration
    with patch.dict(os.environ, {"GITHUB_PERSONAL_ACCESS_TOKEN": "gh_test_valid_key123"}):
        config = GitHubMcpConfig(_env_file=None, GITHUB_PERSONAL_ACCESS_TOKEN="gh_test_valid_key123")  # type: ignore[call-arg]
        params = config.get_connection_config()
        github = params["github"]
        assert github["command"] == "npx"
        assert github["args"] == ["-y", "@modelcontextprotocol/server-github"]
        assert github["env"] is not None
        assert github["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "gh_test_valid_key123"  # noqa: S105


def test_e2b_config_success() -> None:
    # Test valid configuration
    with patch.dict(os.environ, {"E2B_API_KEY": "e2b_valid_key123"}):
        config = E2bMcpConfig(_env_file=None, E2B_API_KEY="e2b_valid_key123")  # type: ignore[call-arg]
        params = config.get_connection_config()
        e2b = params["e2b"]
        assert e2b["command"] == "npx"
        assert e2b["args"] == ["-y", "@e2b/mcp-server"]
        assert e2b["env"] is not None
        assert e2b["env"]["E2B_API_KEY"] == "e2b_valid_key123"


def test_mcp_client_manager_sanitization() -> None:
    # Test that explicitly defined safe keys are kept while secrets are dropped.
    test_env = {
        "PATH": "/usr/bin:/bin",
        "NORMAL_VAR": "value",
        "SUDO_COMMAND": "secret_injection",
        "SUDO_USER": "root"
    }

    with patch.dict(os.environ, test_env, clear=True):
        manager = McpClientManager()
        sanitized = manager._sanitize_environment()

        assert "PATH" in sanitized
        assert "NORMAL_VAR" not in sanitized  # Since we are strictly whitelisting SAFE_ENV_KEYS
        assert "SUDO_COMMAND" not in sanitized
        assert "SUDO_USER" not in sanitized


@pytest.mark.asyncio
async def test_mcp_client_manager_context() -> None:
    # Test that the context manager yields a client with correct parameters
    with patch.dict(os.environ, {"E2B_API_KEY": "e2b_test_key123", "GITHUB_PERSONAL_ACCESS_TOKEN": "gh_test_key123", "SUDO_CMD": "secret"}):
        manager = McpClientManager()

        with patch("src.mcp_router.manager.E2bMcpConfig") as mock_e2b_config_cls, \
             patch("src.mcp_router.manager.GitHubMcpConfig") as mock_gh_config_cls:

            mock_e2b_instance = mock_e2b_config_cls.return_value
            mock_e2b_instance.get_connection_config.return_value = {
                "e2b": {"command": "npx", "args": [], "env": {"E2B_API_KEY": "e2b_test_key123"}, "transport": "stdio"}
            }

            mock_gh_instance = mock_gh_config_cls.return_value
            mock_gh_instance.get_connection_config.return_value = {
                "github": {"command": "npx", "args": [], "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "gh_test_key123"}, "transport": "stdio"}
            }

            # We mock the MultiServerMCPClient to avoid actually starting node processes
            with patch("src.mcp_router.manager.MultiServerMCPClient") as mock_client_cls:
                async with manager.get_client() as _client:
                    mock_client_cls.assert_called_once()

                    # Check that the client was initialized with the combined configuration
                    call_args = mock_client_cls.call_args[0][0]
                    assert "e2b" in call_args
                    assert "github" in call_args

                    e2b_config = call_args["e2b"]
                    assert e2b_config["env"]["E2B_API_KEY"] == "e2b_test_key123"

                    gh_config = call_args["github"]
                    assert gh_config["env"]["GITHUB_PERSONAL_ACCESS_TOKEN"] == "gh_test_key123"  # noqa: S105


@pytest.mark.asyncio
async def test_get_github_read_tools_filtering() -> None:
    # Test that get_github_read_tools successfully filters out write operations.
    from collections import namedtuple
    MockTool = namedtuple("MockTool", ["name", "description"])

    # We will mock tools coming from a MultiServerMCPClient
    dummy_tools = [
        MockTool(name="github_get_file_content", description="Read file"),
        MockTool(name="github_push_commit", description="Push a commit"),
        MockTool(name="github_create_pull_request", description="Create PR"),
        MockTool(name="github_search_repositories", description="Search repos"),
        MockTool(name="e2b_run_code", description="Run arbitrary code"),
    ]

    # Create a mock async context manager for manager.get_client()
    class MockClient:
        async def get_tools(self) -> list[Any]:
            return dummy_tools

    class MockContextManager:
        async def __aenter__(self) -> MockClient:
            return MockClient()
        async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            pass

    with patch.object(McpClientManager, "get_client", return_value=MockContextManager()):
        filtered_tools = await get_github_read_tools()

        tool_names = [t.name for t in filtered_tools]

        # Should include safe read tools
        assert "github_get_file_content" in tool_names
        assert "github_search_repositories" in tool_names

        # Should explicitly exclude write tools and non-github tools
        assert "github_push_commit" not in tool_names
        assert "github_create_pull_request" not in tool_names
        assert "e2b_run_code" not in tool_names
        assert len(filtered_tools) == 2
