from collections.abc import Sequence

from langchain_core.tools import BaseTool

from src.mcp_router.manager import McpClientManager


async def get_e2b_tools() -> Sequence[BaseTool]:
    """Retrieves the E2B tools from the MCP server with proper error handling."""
    manager = McpClientManager()
    try:
        async with manager.get_client() as client:
            all_tools = await client.get_tools()
            return [t for t in all_tools if getattr(t, "server_name", "") == "e2b"]
    except Exception:
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Failed to retrieve E2B tools from MCP server. Tools will be disabled")
        return []


async def get_github_read_tools() -> Sequence[BaseTool]:
    """Retrieves and filters read-only tools from the GitHub MCP server."""
    from src.config import settings
    manager = McpClientManager()

    try:
        async with manager.get_client() as client:
            all_tools = await client.get_tools()

            # Filter tools:
            # 1. Must come from the "github" server
            # 2. Must be in the explicitly allowed non-destructive list
            return [
                t for t in all_tools
                if getattr(t, "server_name", "") == "github" and t.name in settings.tools.github_allowed_read_tools
            ]
    except Exception:
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Failed to retrieve GitHub read tools from MCP server. Tools will be disabled")
        return []
