from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.tools import StructuredTool

from src.domain_models.mcp_config import McpServerConfig
from src.services.mcp_client_manager import McpClientManager


@pytest.mark.asyncio
async def test_mcp_client_manager_initialization() -> None:
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
async def test_mcp_client_manager_timeout() -> None:
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


@pytest.mark.asyncio
async def test_mcp_client_manager_get_readonly_tools_truncation() -> None:
    config = McpServerConfig(
        server_name="github",
        command="echo",
        args=["hello"],
        env={}
    )
    manager = McpClientManager(config=config)

    # Mock tool
    async def mock_arun(*args, **kwargs):
        return "A" * 60000

    def mock_run(*args, **kwargs):
        return "A" * 60000

    from pydantic import BaseModel, Field
    class MockArgs(BaseModel):
        path: str = Field(...)

    tool = StructuredTool(
        name="github_get_file_content",
        description="mock tool",
        args_schema=MockArgs,
        func=mock_run,
        coroutine=mock_arun,
    )
    # Use object setattr bypass for Pydantic v2 strictness
    object.__setattr__(tool, "server_name", "github")

    with patch("langchain_mcp_adapters.client.MultiServerMCPClient.get_tools", new_callable=AsyncMock) as mock_tools:
        mock_tools.return_value = [tool]

        async with manager as m:
            tools = await m.get_readonly_tools("github")
            assert len(tools) == 1
            proxied_tool = tools[0]
            assert proxied_tool.name == "github_get_file_content"

            # Execute tool to verify truncation
            res = await proxied_tool.ainvoke({"path": "test"})
            assert isinstance(res, str)
            assert len(res) > 50000
            assert "...[Content truncated, exceeded 50000 characters]..." in res
            assert len(res) <= 50000 + len("\n\n...[Content truncated, exceeded 50000 characters]...")

@pytest.mark.asyncio
async def test_mcp_client_manager_get_readonly_tools_filtering() -> None:
    config = McpServerConfig(
        server_name="github",
        command="echo",
        args=["hello"],
        env={}
    )
    manager = McpClientManager(config=config)

    from pydantic import BaseModel, Field
    class MockArgs(BaseModel):
        path: str = Field(...)

    def mock_run(*args, **kwargs):
        return "ok"

    t1 = StructuredTool(name="github_get_file_content", description="mock", args_schema=MockArgs, func=mock_run)
    t2 = StructuredTool(name="github_search_repositories", description="mock", args_schema=MockArgs, func=mock_run)
    t3 = StructuredTool(name="github_create_branch", description="mock", args_schema=MockArgs, func=mock_run)
    t4 = StructuredTool(name="push_commit", description="mock", args_schema=MockArgs, func=mock_run)

    with patch("langchain_mcp_adapters.client.MultiServerMCPClient.get_tools", new_callable=AsyncMock) as mock_tools:
        mock_tools.return_value = [t1, t2, t3, t4]

        async with manager as m:
            tools = await m.get_readonly_tools("github")
            assert len(tools) == 2
            names = [t.name for t in tools]
            assert "github_get_file_content" in names
            assert "github_search_repositories" in names
            assert "github_create_branch" not in names
            assert "push_commit" not in names
