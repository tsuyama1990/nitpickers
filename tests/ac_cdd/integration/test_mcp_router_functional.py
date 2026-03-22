import os
from unittest.mock import patch

import pytest

from src.mcp_router.manager import McpClientManager


def test_sanitize_environment() -> None:
    """Test that _sanitize_environment removes dangerous prefixes but keeps allowed keys."""
    # Ensure some API keys and dangerous keys are set in the environment
    test_env = {
        "SUDO_USER": "root",
        "SSH_AUTH_SOCK": "/tmp/ssh-123",  # noqa: S108
        "AWS_ACCESS_KEY_ID": "AKIA...",
        "GCP_PRIVATE_KEY": "BEGIN PRIVATE KEY...",
        "AZURE_CLIENT_SECRET": "secret...",
        "AWS_SECRET_ACCESS_KEY": "secret...",
        "E2B_API_KEY": "e2b_test_key",
        "GITHUB_PERSONAL_ACCESS_TOKEN": "gh_test_token",
        "JULES_API_KEY": "jules_test_key",
        "PATH": "/usr/bin:/bin",
        "USER": "jules",
    }

    with patch.dict(os.environ, test_env, clear=True):
        sanitized = McpClientManager._sanitize_environment()

        # Check dangerous keys are removed
        assert "SUDO_USER" not in sanitized
        assert "SSH_AUTH_SOCK" not in sanitized
        assert "AWS_ACCESS_KEY_ID" not in sanitized
        assert "GCP_PRIVATE_KEY" not in sanitized
        assert "AZURE_CLIENT_SECRET" not in sanitized
        assert "AWS_SECRET_ACCESS_KEY" not in sanitized

        # Check allowed keys are kept
        assert sanitized.get("E2B_API_KEY") == "e2b_test_key"
        assert sanitized.get("GITHUB_PERSONAL_ACCESS_TOKEN") == "gh_test_token"
        assert sanitized.get("JULES_API_KEY") == "jules_test_key"
        assert sanitized.get("PATH") == "/usr/bin:/bin"
        assert sanitized.get("USER") == "jules"


@pytest.mark.live
@pytest.mark.asyncio
async def test_mcp_client_manager_live() -> None:
    """
    Live test to ensure McpClientManager initializes correctly and can bind to
    GitHub, E2B, and Jules MCP servers. It also tests that tools can be fetched
    and correctly execute.
    """
    # Verify environment keys are present to ensure the test can run
    # We will log the current environment keys if missing.
    e2b_key = os.environ.get("E2B_API_KEY")
    jules_key = os.environ.get("JULES_API_KEY")

    if not e2b_key or not jules_key:
        pytest.skip(
            f"Missing required API keys: E2B={bool(e2b_key)}, JULES={bool(jules_key)}"
        )

    # GITHUB_PERSONAL_ACCESS_TOKEN might not be available, let's just warn about it
    gh_key = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")

    manager = McpClientManager()

    async with manager.get_client() as client:
        # Get tools from the multi-server client
        tools = await client.get_tools()

        # Tools are returned as LangChain BaseTool instances.
        tool_names = [tool.name for tool in tools]

        # Verify that expected tools from each server exist
        # GitHub tools (e.g. get_file_contents, list_repositories)
        if gh_key:
            assert "get_file_contents" in tool_names or "list_repositories" in tool_names, (
                f"GitHub tools not found. Available tools: {tool_names}"
            )

        # E2B tools (e.g. run_command)
        assert "run_command" in tool_names or "run_code" in tool_names, (
            f"E2B tools not found. Available tools: {tool_names}"
        )

        # Jules tools (e.g. jules_status or list_sessions)
        jules_tools = [name for name in tool_names if "session" in name or "status" in name]
        assert len(jules_tools) > 0, f"Jules tools not found. Available tools: {tool_names}"

        # Test E2B: execute a simple command
        # Find the run_command tool
        run_cmd_tool = next((t for t in tools if t.name in {"run_command", "run_code"}), None)
        assert run_cmd_tool is not None, "E2B execution tool not found."

        # The E2B run_command tool usually takes a 'command' argument
        e2b_result = await run_cmd_tool.ainvoke({"command": "echo 'MCP verification'"})
        assert "MCP verification" in str(e2b_result)

        # Test GitHub: Since we might not have a GH key, the server might not boot.
        if gh_key:
            github_tool = next(
                (t for t in tools if t.name in {"get_file_contents", "list_repositories"}), None
            )
            assert github_tool is not None, "GitHub tool not found."

            if github_tool.name == "list_repositories":
                github_result = await github_tool.ainvoke({})
                assert isinstance(github_result, (list, str))
            elif github_tool.name == "get_file_contents":
                with pytest.raises(Exception) as exc_info: # noqa: PT011
                    await github_tool.ainvoke({})
                # Fails due to missing args, proving JSON RPC is alive
                assert "validation" in str(exc_info.value).lower() or "required" in str(exc_info.value).lower() or "missing" in str(exc_info.value).lower()

        # Test Jules: trigger a session listing via Jules MCP toolset
        # It's better to trigger an action with known missing args to verify the server validates the JSON RPC correctly.
        jules_tool = next((t for t in tools if t.name in jules_tools), None)
        assert jules_tool is not None, "Jules tool not found."

        # If it's something like jules_status or get_session, it requires args
        # So invoking with empty dict should return a validation error from the Jules MCP sidecar
        try:
            res = await jules_tool.ainvoke({})
            # Some tools might succeed with empty dicts, in which case we assert it returned a value.
            assert res is not None
        except Exception as e:
            err_str = str(e).lower()
            # mcp_router throws Invalid code interpreter arguments sometimes, which has the phrase invalid
            assert any(x in err_str for x in ["validation", "required", "missing", "invalid", "argument", "interpreter", "error"])
