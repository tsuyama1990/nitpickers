from collections.abc import Sequence

from langchain_core.tools import BaseTool

from src.mcp_router.manager import McpClientManager


async def get_e2b_tools() -> Sequence[BaseTool]:
    """Retrieves the E2B tools from the MCP server with proper error handling."""
    import asyncio
    import logging
    logger = logging.getLogger(__name__)
    manager = McpClientManager()

    max_retries = 3
    base_delay = 1.0

    for attempt in range(max_retries):
        try:
            async with manager.get_client() as client:
                all_tools = await asyncio.wait_for(client.get_tools(), timeout=10.0)
                return [t for t in all_tools if getattr(t, "server_name", "") == "e2b"]
        except Exception as e:
            logger.warning(f"Error fetching E2B tools (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2**attempt))
            else:
                logger.exception("Failed to retrieve E2B tools from MCP server after retries. Tools will be disabled")
    return []


async def get_github_read_tools(allowed_tools: set[str] | None = None) -> Sequence[BaseTool]:
    """Retrieves and filters read-only tools from the GitHub MCP server."""
    import asyncio
    import logging

    logger = logging.getLogger(__name__)
    manager = McpClientManager()

    max_retries = 3
    base_delay = 1.0

    # Default to explicitly known safe read operations to avoid circular dependencies
    if allowed_tools is None:
        allowed_tools = {"get_file_content", "search_repositories", "get_issue"}

    for attempt in range(max_retries):
        try:
            async with manager.get_client() as client:
                all_tools = await asyncio.wait_for(client.get_tools(), timeout=10.0)

                # Filter tools:
                # 1. Must come from the "github" server
                # 2. Must be in the explicitly allowed non-destructive list
                return [
                    t for t in all_tools
                    if getattr(t, "server_name", "") == "github" and t.name in allowed_tools
                ]
        except Exception as e:
            logger.warning(f"Error fetching GitHub read tools (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2**attempt))
            else:
                logger.exception("Failed to retrieve GitHub read tools from MCP server after retries. Tools will be disabled")
    return []
