import asyncio
import logging
from contextlib import AbstractAsyncContextManager
from typing import Any

from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.types import JSONRPCMessage

from src.domain_models.config import McpServerConfig
from src.domain_models.execution import ToolExecutionError

logger = logging.getLogger(__name__)


class McpClientManager:
    """
    Manages the lifecycle of an MCP server connection using the Stdio transport.
    """

    def __init__(self, config: McpServerConfig) -> None:
        self.config = config
        self._server_params = StdioServerParameters(
            command=self.config.npx_path,
            args=["-y", "@e2b/mcp-server"],
            env={"E2B_API_KEY": self.config.e2b_api_key.get_secret_value()},
        )
        self._stdio_context: (
            AbstractAsyncContextManager[
                tuple[
                    MemoryObjectReceiveStream[JSONRPCMessage | Exception],
                    MemoryObjectSendStream[JSONRPCMessage],
                ]
            ]
            | None
        ) = None
        self._read: MemoryObjectReceiveStream[JSONRPCMessage | Exception] | None = None
        self._write: MemoryObjectSendStream[JSONRPCMessage] | None = None
        self._session: ClientSession | None = None
        self._session_context: AbstractAsyncContextManager[ClientSession] | None = None

    async def __aenter__(self) -> "McpClientManager":
        """Establishes connection to the MCP server."""
        logger.info("Initializing MCP Stdio connection...")
        try:
            self._stdio_context = stdio_client(self._server_params)
            self._read, self._write = await self._stdio_context.__aenter__()

            self._session_context = ClientSession(self._read, self._write) # type: ignore[arg-type]
            self._session = await self._session_context.__aenter__()

            await self._session.initialize()
            logger.info("MCP server initialized successfully.")
        except Exception as e:
            await self._cleanup()
            msg = f"Failed to connect to MCP server: {e}"
            logger.exception(msg)
            raise ToolExecutionError(message=msg, tool_name="mcp_server_init", code=-1) from e
        else:
            return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Cleans up the MCP server connection."""
        await self._cleanup()

    async def _cleanup(self) -> None:
        """Internal cleanup logic to close the session and stdio transports."""
        logger.info("Cleaning up MCP Stdio connection...")
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing MCP session: {e}")
            finally:
                self._session_context = None
                self._session = None

        if self._stdio_context:
            try:
                await self._stdio_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing stdio transport: {e}")
            finally:
                self._stdio_context = None
                self._read = None
                self._write = None

    async def get_tools(self) -> list[Any]:
        """Retrieves LangChain-compatible tools from the active MCP session."""
        if not self._session:
            msg = "MCP session is not initialized."
            raise ToolExecutionError(message=msg, tool_name="get_tools", code=-1)

        try:
            return await asyncio.wait_for(
                load_mcp_tools(self._session), timeout=self.config.timeout_seconds
            )
        except TimeoutError as e:
            msg = "Timeout while fetching tools from MCP server."
            raise ToolExecutionError(message=msg, tool_name="get_tools", code=408) from e
        except Exception as e:
            msg = f"Error fetching tools: {e}"
            raise ToolExecutionError(message=msg, tool_name="get_tools", code=500) from e
