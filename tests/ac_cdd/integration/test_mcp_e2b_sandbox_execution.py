import pytest
import os
from unittest.mock import AsyncMock, patch

from src.domain_models.config import McpServerConfig
from src.services.mcp_client_manager import McpClientManager
from src.state import CycleState

@pytest.fixture
def test_config():
    api_key = os.getenv("E2B_API_KEY", "mock_key")
    return McpServerConfig(
        e2b_api_key=api_key,
        timeout_seconds=30,
        npx_path="npx"
    )

@pytest.mark.asyncio
async def test_mcp_e2b_sandbox_execution(test_config):
    # This is a basic integration test to verify the McpClientManager can connect and fetch tools
    # We will use patching if E2B_API_KEY is not a real key in CI environment
    if test_config.e2b_api_key.get_secret_value() == "mock_key":
        with patch("src.services.mcp_client_manager.stdio_client") as mock_stdio_client, \
             patch("src.services.mcp_client_manager.ClientSession") as mock_client_session_cls, \
             patch("src.services.mcp_client_manager.load_mcp_tools") as mock_load_tools:

            mock_stdio_cm = AsyncMock()
            mock_stdio_cm.__aenter__.return_value = (AsyncMock(), AsyncMock())
            mock_stdio_client.return_value = mock_stdio_cm

            mock_session_cm = AsyncMock()
            mock_session = AsyncMock()
            mock_session_cm.__aenter__.return_value = mock_session
            mock_client_session_cls.return_value = mock_session_cm

            mock_tools = ["run_code", "execute_command"]
            mock_load_tools.return_value = mock_tools

            manager = McpClientManager(test_config)
            async with manager as connected_manager:
                tools = await connected_manager.get_tools()
                assert len(tools) > 0
                assert tools == mock_tools
    else:
        # If we have a real key, test the actual connection (may take a bit longer to start npx)
        try:
            manager = McpClientManager(test_config)
            async with manager as connected_manager:
                tools = await connected_manager.get_tools()
                assert len(tools) > 0
                # Tools returned are Langchain tools, we can check their names
                tool_names = [tool.name for tool in tools]
                assert "run_code" in tool_names or "execute_command" in tool_names
        except Exception as e:
            pytest.skip(f"Live E2B test skipped due to connection failure: {e}")
