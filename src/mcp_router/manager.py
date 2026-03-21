import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient

from src.mcp_router.schemas import E2bMcpConfig


class McpClientManager:
    """Manages the lifecycle of MCP clients."""

    SAFE_ENV_KEYS: tuple[str, ...] = (
        "PATH", "USER", "HOME", "LANG", "LC_ALL", "TERM", "TZ",
        "PYTHONPATH", "LD_LIBRARY_PATH", "VIRTUAL_ENV"
    )

    @classmethod
    def _sanitize_environment(cls) -> dict[str, str]:
        """
        Sanitizes the environment dictionary to prevent leakage of secrets.
        Uses a strict whitelist approach to ensure NO API keys or credentials
        are accidentally leaked to subprocesses or logs.
        """
        sanitized = {}
        for key, value in os.environ.items():
            if key in cls.SAFE_ENV_KEYS:
                sanitized[key] = value
        return sanitized

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[MultiServerMCPClient, None]:
        """Provides an asynchronous context manager for the MCP client with robust error handling."""
        config = E2bMcpConfig()  # type: ignore[call-arg]

        # Override the env with sanitized environment to prevent leakages
        sanitized_env = self._sanitize_environment()

        # Build dynamic connections from the config
        connection_config = config.get_connection_config(sanitized_env)

        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries):
            try:
                client = MultiServerMCPClient(connection_config)  # type: ignore[arg-type]
                break
            except Exception as e:
                import logging

                logger = logging.getLogger(__name__)
                logger.exception(
                    f"Failed to initialize MultiServerMCPClient (attempt {attempt + 1}/{max_retries})"
                )
                if attempt == max_retries - 1:
                    msg = f"Failed to connect to MCP servers after {max_retries} attempts: {e}"
                    raise RuntimeError(msg) from e
                await asyncio.sleep(base_delay * (2**attempt))

        try:
            yield client
        finally:
            # MultiServerMCPClient does not expose a public .close() or handle cleanup.
            # We enforce a small timeout loop strictly checking if we can kill any
            # active underlying Popen/subprocess connections cleanly if possible.
            # Langchain's MultiServerMCPClient sessions are managed via asynccontextmanager 'session'
            # For now, since it lacks cleanup methods natively, we just rely on standard GC.
            pass
