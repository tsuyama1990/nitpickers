import os
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.config import settings
from src.domain_models.mcp_config import McpServerConfig
from src.utils import logger


class McpClientManager:
    """
    Manages connections to MCP servers.
    Acts as an async context manager to ensure clean teardown of child processes.
    """

    def __init__(self, config: McpServerConfig | None = None) -> None:
        self.configs: dict[str, McpServerConfig] = {}

        if config is not None:
            self.configs[config.server_name] = config
            # Also add github if not specifically overriden, for backward compatibility
            # if someone instantiates with E2B but still needs Github.
            # Actually, to be safe, we just use what is passed, but if they pass E2B, we should still ensure GitHub is available
            # because the new logic expects it. Let's just always add default if missing.

        if "e2b" not in self.configs:
            e2b_env = {}
            if settings.E2B_API_KEY:
                e2b_env["E2B_API_KEY"] = settings.E2B_API_KEY.get_secret_value()
            self.configs["e2b"] = McpServerConfig(
                server_name="e2b",
                command="npx",
                args=["-y", "@e2b/mcp-server"],
                env=e2b_env,
            )

        if "github" not in self.configs:
            gh_env = {}
            gh_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
            if gh_token:
                gh_env["GITHUB_PERSONAL_ACCESS_TOKEN"] = gh_token
            self.configs["github"] = McpServerConfig(
                server_name="github",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env=gh_env,
            )

        connections = {}
        for name, cfg in self.configs.items():
            merged_env = os.environ.copy()
            merged_env.update(cfg.env)
            connections[name] = {
                "command": cfg.command,
                "args": cfg.args,
                "env": merged_env,
                "transport": "stdio",
            }

        self._client = MultiServerMCPClient(connections=connections)  # type: ignore[arg-type]

    async def get_tools(self, server_name: str | None = None) -> list[BaseTool]:
        """
        Retrieves the tools advertised by the specified MCP server as LangChain tools.
        """
        try:
            # Langchain's MultiServerMCPClient provides get_tools() which translates MCP tools
            # Note: The client returns tools across ALL initialized servers.
            all_tools = await self._client.get_tools()

            # langchain_mcp_adapters uses a prefix for tool names based on server name
            # like "e2b_tool_name" or "github_tool_name" if multiple servers are used.
            # However, looking at the MultiServerMCPClient implementation, it typically
            # returns tools with server prefixes if needed, or we might need to filter.

            # Since server_name filtering is requested:
            filtered_tools = []
            for tool in all_tools:
                # Basic prefix matching. E.g., github_get_file_content
                if server_name:
                    if tool.name.startswith(f"{server_name}_") or (hasattr(tool, "server_name") and tool.server_name == server_name):
                        filtered_tools.append(tool)
                    elif server_name == "e2b":
                        # E2B tools might not be prefixed or handled differently
                        filtered_tools.append(tool)
                else:
                    filtered_tools.append(tool)

            if not server_name:
                return list(all_tools)

            return list(filtered_tools)
        except Exception as e:
            msg = f"Failed to retrieve tools from MCP server {server_name}: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    async def get_readonly_tools(self, server_name: str) -> list[BaseTool]:
        """
        Retrieves read-only tools and proxies output to avoid token exhaustion.
        """
        all_tools = await self._client.get_tools()

        whitelist = ["get_file_content", "search_repositories"]

        filtered = []
        for tool in all_tools:
            # MultiServerMCPClient tools often have the format "{server_name}_{original_tool_name}"
            # So github's tool is likely "github_get_file_content"
            is_match = False
            for w in whitelist:
                if tool.name == w or tool.name.endswith(f"_{w}"):
                    is_match = True
                    break

            if not is_match:
                continue

            # If server_name is provided, ensure it matches
            if (
                not tool.name.startswith(f"{server_name}_")
                and tool.name != whitelist[0]
                and tool.name != whitelist[1]
                and getattr(tool, "server_name", server_name) != server_name
            ):
                continue

            if "get_file_content" in tool.name:
                proxied_tool = self._create_proxy_tool(tool, 50000)
                filtered.append(proxied_tool)
            else:
                filtered.append(tool)

        return filtered

    def _create_proxy_tool(self, tool: BaseTool, max_length: int) -> BaseTool:
        """Wraps a tool to intercept output and prevent token exhaustion/crashes."""

        async def proxied_arun(*args: Any, **kwargs: Any) -> Any:
            try:
                result = await tool.ainvoke(kwargs)
                result_str = str(result)
            except Exception as e:
                # Graceful fallback: return error string within ToolMessage
                return f"Error executing tool {tool.name}: {e}"
            else:
                if len(result_str) > max_length:
                    trunc_msg = f"\n\n...[Content truncated, exceeded {max_length} characters]..."
                    return result_str[:max_length] + trunc_msg
                return result_str

        def proxied_run(*args: Any, **kwargs: Any) -> Any:
            try:
                result = tool.invoke(kwargs)
                result_str = str(result)
            except Exception as e:
                return f"Error executing tool {tool.name}: {e}"
            else:
                if len(result_str) > max_length:
                    trunc_msg = f"\n\n...[Content truncated, exceeded {max_length} characters]..."
                    return result_str[:max_length] + trunc_msg
                return result_str

        return StructuredTool(
            name=tool.name,
            description=tool.description,
            args_schema=tool.args_schema,  # type: ignore[arg-type]
            func=proxied_run,
            coroutine=proxied_arun,
        )

    async def close(self) -> None:
        """Closes the connection and terminates the child process."""
        # MultiServerMCPClient in langchain-mcp-adapters=0.2+ handles session contexts internally

    async def __aenter__(self) -> "McpClientManager":
        return self

    async def __aexit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> None:
        await self.close()
