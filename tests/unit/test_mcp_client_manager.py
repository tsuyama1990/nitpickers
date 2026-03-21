from unittest.mock import AsyncMock, patch

import pytest

from src.domain_models.mcp_config import McpServerConfig
from src.services.mcp_client_manager import McpClientManager


@pytest.mark.asyncio
async def test_mcp_client_manager_initialization():
    config = McpServerConfig(
        server_name="test_server",
        command="echo",
        args=["hello"],
        env={"TEST_KEY": "test_val"}
    )
    manager = McpClientManager(config=config)

    with patch("langchain_mcp_adapters.client.MultiServerMCPClient.get_tools", new_callable=AsyncMock) as mock_tools:
        mock_tools.return_value = []

        async with manager as m:
            tools = await m.get_tools()
            assert isinstance(tools, list)

@pytest.mark.asyncio
async def test_mcp_client_manager_timeout():
    config = McpServerConfig(
        server_name="test_server",
        command="sleep",
        args=["10"],
        timeout_seconds=1
    )
    manager = McpClientManager(config=config)

    with patch("langchain_mcp_adapters.client.MultiServerMCPClient.get_tools", new_callable=AsyncMock) as mock_tools:
        mock_tools.side_effect = Exception("Timeout Error")

        with pytest.raises(RuntimeError) as exc_info:
            async with manager as m:
                await m.get_tools()

        assert "Failed to retrieve tools from MCP server" in str(exc_info.value)
