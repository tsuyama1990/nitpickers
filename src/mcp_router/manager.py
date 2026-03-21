import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient

from src.mcp_router.schemas import E2bMcpConfig


class McpClientManager:
    """Manages the lifecycle of MCP clients."""

    @staticmethod
    def _sanitize_environment() -> dict[str, str]:
        """Sanitizes the environment dictionary to prevent leakage of secrets."""
        env = dict(os.environ)
        # Prevent API key leakage via unexpanded SUDO_ variables logged by langchain-mcp-adapters
        keys_to_remove = [k for k in env if k.startswith("SUDO_")]
        for key in keys_to_remove:
            env.pop(key, None)
        return env

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[MultiServerMCPClient, None]:
        """Provides an asynchronous context manager for the MCP client."""
        config = E2bMcpConfig()  # type: ignore[call-arg]
        params = config.get_stdio_parameters()

        # Override the env with sanitized environment to prevent leakages
        sanitized_env = self._sanitize_environment()
        # Merge back specific api keys required for execution
        sanitized_env.update(params.env or {})

        connection_config = {
            "e2b": {
                "command": params.command,
                "args": params.args,
                "env": sanitized_env,
                "transport": "stdio",
            }
        }

        client = MultiServerMCPClient(connection_config)  # type: ignore[arg-type]

        try:
            yield client
        finally:
            # MultiServerMCPClient doesn't have a close method, it manages sessions lazily
            # We wait a tiny bit to ensure subprocesses are cleaned up if any were spawned
            await asyncio.sleep(0.1)
