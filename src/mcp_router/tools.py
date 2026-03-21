from collections.abc import Sequence

from langchain_core.tools import BaseTool

from src.mcp_router.manager import McpClientManager


async def _fetch_tools_with_retry(server_name: str, allowed_tools: set[str] | None = None) -> Sequence[BaseTool]:
    """
    Internal helper to fetch and filter tools from a specific MCP server with exponential backoff.

    Args:
        server_name: The name of the server mapping (e.g., 'e2b', 'github').
        allowed_tools: A set of tool names to whitelist. If None, all tools from the server are allowed.

    Returns:
        Sequence[BaseTool]: A filtered list of available tools.
    """
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

                return [
                    t for t in all_tools
                    if getattr(t, "server_name", "") == server_name
                    and (allowed_tools is None or t.name in allowed_tools)
                ]
        except Exception as e:
            logger.warning(f"Error fetching {server_name.upper()} tools (attempt {attempt+1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(base_delay * (2**attempt))
            else:
                logger.exception(f"Failed to retrieve {server_name.upper()} tools from MCP server after retries. Tools will be disabled.")

    return []


async def get_e2b_tools() -> Sequence[BaseTool]:
    """Retrieves the E2B tools from the MCP server with proper error handling."""
    return await _fetch_tools_with_retry("e2b")


async def get_github_read_tools(allowed_tools: set[str] | None = None) -> Sequence[BaseTool]:
    """Retrieves and filters read-only tools from the GitHub MCP server."""
    # Default to explicitly known safe read operations to avoid circular dependencies
    if allowed_tools is None:
        allowed_tools = {"get_file_content", "search_repositories", "get_issue"}

    return await _fetch_tools_with_retry("github", allowed_tools=allowed_tools)


async def get_github_write_tools() -> Sequence[BaseTool]:
    """Retrieves and filters write-only mutating tools from the GitHub MCP server."""
    allowed_tools = {"push_commit", "create_pull_request", "create_branch"}
    return await _fetch_tools_with_retry("github", allowed_tools=allowed_tools)


async def get_jules_tools() -> Sequence[BaseTool]:
    """Retrieves the Jules tools from the MCP server."""
    return await _fetch_tools_with_retry("jules")
