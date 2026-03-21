import os
from typing import Any

from langchain_core.tools import BaseTool
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
        if config is None:
            # Default to E2B MCP Server config if not provided
            env_vars = {}
            if settings.E2B_API_KEY:
                env_vars["E2B_API_KEY"] = settings.E2B_API_KEY.get_secret_value()

            self.config = McpServerConfig(
                server_name="e2b",
                command="npx",
                args=["-y", "@e2b/mcp-server"],
                env=env_vars,
            )
        else:
            self.config = config

        # Merge current OS environment variables to preserve paths and binaries (like npx)
        merged_env = os.environ.copy()
        merged_env.update(self.config.env)

        # MultiServerMCPClient from langchain_mcp_adapters manages connection per tool call or context manager
        self._client = MultiServerMCPClient(
            connections={
                self.config.server_name: {
                    "command": self.config.command,
                    "args": self.config.args,
                    "env": merged_env,
                    "transport": "stdio",
                }
            }
        )

    async def get_tools(self, server_name: str | None = None) -> list[BaseTool]:
        """
        Retrieves the tools advertised by the specified MCP server as LangChain tools.
        """
        target_server = server_name or self.config.server_name

        try:
            # Langchain's MultiServerMCPClient provides get_tools() which translates MCP tools
            tools = await self._client.get_tools()
        except Exception as e:
            msg = f"Failed to retrieve tools from MCP server {target_server}: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e

        return list(tools)

    async def close(self) -> None:
        """Closes the connection and terminates the child process."""
        # MultiServerMCPClient in langchain-mcp-adapters=0.2+ handles session contexts internally

    async def __aenter__(self) -> "McpClientManager":
        return self

    async def __aexit__(
        self, exc_type: Any, exc_val: Any, exc_tb: Any
    ) -> None:
        await self.close()
