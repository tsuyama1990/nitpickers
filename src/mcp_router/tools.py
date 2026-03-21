from collections.abc import Sequence

from langchain_core.tools import BaseTool

from src.mcp_router.manager import McpClientManager


async def get_e2b_tools() -> Sequence[BaseTool]:
    """Retrieves the E2B tools from the MCP server with proper error handling."""
    manager = McpClientManager()
    try:
        async with manager.get_client() as client:
            return await client.get_tools()
    except Exception:
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Failed to retrieve tools from MCP server. Tools will be disabled")
        return []
