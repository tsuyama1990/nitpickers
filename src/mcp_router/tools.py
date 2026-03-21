from collections.abc import Sequence

from langchain_core.tools import BaseTool

from src.mcp_router.manager import McpClientManager


async def get_e2b_tools() -> Sequence[BaseTool]:
    """Retrieves the E2B tools from the MCP server with proper error handling."""
    manager = McpClientManager()
    try:
        async with manager.get_client() as client:
            # We filter specifically for the e2b server's tools in a multi-server setup
            tools = await client.get_tools()

            # The tool names from langchain_mcp_adapters are typically namespaced if there are multiple servers,
            # but MultiServerMCPClient might just return all of them.
            # E2B tools generally include run_code, execute_command, etc.
            # We don't strictly filter out GitHub tools here, but for safety, we should.
            # For simplicity, we'll return tools that belong to E2B (assuming we can distinguish,
            # or we return all and rely on get_github_read_tools to restrict github tools).
            # Actually, MultiServerMCPClient get_tools returns a list of all tools from all connected servers.
            # The names are prefixed with the server name (e.g. "e2b_run_code", "github_get_file_content")
            # Wait, let's just return all tools that start with "e2b_" or where name doesn't start with "github_"
            return [t for t in tools if getattr(t, "name", "").startswith("e2b_") or not getattr(t, "name", "").startswith("github_")]
    except Exception:
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Failed to retrieve tools from MCP server. Tools will be disabled")
        return []

async def get_github_read_tools() -> Sequence[BaseTool]:
    """Retrieves only the read-only GitHub tools from the MCP server."""
    manager = McpClientManager()
    try:
        async with manager.get_client() as client:
            tools = await client.get_tools()

            # The allowed read-only tool names.
            # In MultiServerMCPClient, tools might be prefixed with the server name, e.g. "github_get_file_content".
            # We check if the core name is in our allowed list.
            allowed_core_names = {"get_file_content", "search_repositories", "get_issue", "list_commits", "list_issues", "search_issues", "get_file", "list_branches", "list_pull_requests"}

            safe_tools = []
            for t in tools:
                name = getattr(t, "name", "")

                # If the tool is an E2B tool, we don't include it in the github read tools list.
                # We strictly want github read tools.
                if not name.startswith("github_"):
                    continue

                core_name = name.replace("github_", "", 1)

                # Explicitly block write operations
                if any(write_verb in core_name for write_verb in ["write", "push", "create", "delete", "merge", "update"]):
                    continue

                if core_name in allowed_core_names or "get" in core_name or "list" in core_name or "search" in core_name:
                    safe_tools.append(t)

            return safe_tools

    except Exception:
        import logging

        logger = logging.getLogger(__name__)
        logger.exception("Failed to retrieve GitHub tools from MCP server. Tools will be disabled")
        return []
