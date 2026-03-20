import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.domain_models.config import McpServerConfig
from src.domain_models.execution import ToolExecutionError
from src.services.mcp_client_manager import McpClientManager


@pytest.fixture
def mock_config():
    return McpServerConfig(
        e2b_api_key="mock_key",
        timeout_seconds=5,
        npx_path="npx"
    )


@pytest.mark.asyncio
async def test_mcp_client_manager_init(mock_config):
    manager = McpClientManager(mock_config)
    assert manager.config == mock_config
    assert manager._session is None


@pytest.mark.asyncio
@patch("src.services.mcp_client_manager.stdio_client")
@patch("src.services.mcp_client_manager.ClientSession")
async def test_mcp_client_manager_aenter(mock_client_session_cls, mock_stdio_client, mock_config):
    # Mock the stdio context manager
    mock_stdio_cm = AsyncMock()
    mock_stdio_cm.__aenter__.return_value = (MagicMock(), MagicMock()) # (read, write)
    mock_stdio_client.return_value = mock_stdio_cm

    # Mock the session context manager
    mock_session_cm = AsyncMock()
    mock_session = AsyncMock()
    mock_session_cm.__aenter__.return_value = mock_session
    mock_client_session_cls.return_value = mock_session_cm

    manager = McpClientManager(mock_config)

    async with manager as connected_manager:
        assert connected_manager is manager
        assert connected_manager._session is mock_session
        mock_session.initialize.assert_awaited_once()

    # Verify aexit is called on cleanup
    mock_session_cm.__aexit__.assert_awaited_once()
    mock_stdio_cm.__aexit__.assert_awaited_once()


@pytest.mark.asyncio
@patch("src.services.mcp_client_manager.stdio_client")
async def test_mcp_client_manager_aenter_failure(mock_stdio_client, mock_config):
    # Mock the stdio context manager to raise an exception
    mock_stdio_client.side_effect = Exception("Failed to start")

    manager = McpClientManager(mock_config)

    with pytest.raises(ToolExecutionError) as exc:
        async with manager:
            pass

    assert "Failed to connect to MCP server: Failed to start" in str(exc.value)
    assert exc.value.tool_name == "mcp_server_init"
    assert exc.value.code == -1


@pytest.mark.asyncio
@patch("src.services.mcp_client_manager.stdio_client")
@patch("src.services.mcp_client_manager.ClientSession")
@patch("src.services.mcp_client_manager.load_mcp_tools")
async def test_mcp_client_manager_get_tools(mock_load_tools, mock_client_session_cls, mock_stdio_client, mock_config):
    # Mock the stdio context manager
    mock_stdio_cm = AsyncMock()
    mock_stdio_cm.__aenter__.return_value = (MagicMock(), MagicMock())
    mock_stdio_client.return_value = mock_stdio_cm

    # Mock the session context manager
    mock_session_cm = AsyncMock()
    mock_session = AsyncMock()
    mock_session_cm.__aenter__.return_value = mock_session
    mock_client_session_cls.return_value = mock_session_cm

    # Mock load_tools
    mock_tools = ["tool1", "tool2"]
    mock_load_tools.return_value = mock_tools

    manager = McpClientManager(mock_config)

    async with manager as connected_manager:
        tools = await connected_manager.get_tools()
        assert tools == mock_tools
        mock_load_tools.assert_called_once_with(mock_session)


@pytest.mark.asyncio
async def test_mcp_client_manager_get_tools_uninitialized(mock_config):
    manager = McpClientManager(mock_config)

    with pytest.raises(ToolExecutionError) as exc:
        await manager.get_tools()

    assert "MCP session is not initialized" in str(exc.value)
    assert exc.value.tool_name == "get_tools"
    assert exc.value.code == -1
