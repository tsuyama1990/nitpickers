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
        "PYTHONPATH", "LD_LIBRARY_PATH", "VIRTUAL_ENV",
        "NODE_ENV", "NVM_DIR", "NVM_BIN", "NVM_INC", "NPM_CONFIG_PREFIX"
    )

    @classmethod
    def _sanitize_environment(cls) -> dict[str, str]:
        """
        Sanitizes the environment dictionary to prevent leakage of secrets.
        Uses a strict blacklist approach specifically filtering known credential
        patterns while allowing benign vars, which ensures critical shell vars aren't dropped.
        """
        import re
        sanitized = {}

        # Blacklist any environment variable that contains these substrings
        secret_patterns = re.compile(
            r"(API_KEY|SECRET|PASSWORD|TOKEN|CREDENTIAL|AUTH|KEY|SUDO_)",
            re.IGNORECASE
        )

        for key, value in os.environ.items():
            if secret_patterns.search(key):
                continue
            sanitized[key] = value

        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Sanitized environment. Filtered out {len(os.environ) - len(sanitized)} keys.")
        return sanitized

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[MultiServerMCPClient, None]:  # noqa: C901
        """Provides an asynchronous context manager for the MCP client with robust error handling."""
        config = E2bMcpConfig()  # type: ignore[call-arg]

        # Override the env with sanitized environment to prevent leakages
        sanitized_env = self._sanitize_environment()

        # Build dynamic connections from the config
        connection_config = config.get_connection_config(sanitized_env)

        max_retries = 3
        base_delay = 1.0

        import logging
        logger = logging.getLogger(__name__)

        client = None
        for attempt in range(max_retries):
            try:
                # Add timeout to client initialization itself if possible or wait_for
                # Note: MultiServerMCPClient init is synchronous, but we'll wrap it safely
                client = MultiServerMCPClient(connection_config)
                break
            except ConnectionError as e:
                logger.exception(f"Connection error initializing MultiServerMCPClient (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    msg = f"Connection failed to MCP servers after {max_retries} attempts: {e}"
                    raise ConnectionError(msg) from e
            except Exception as e:
                logger.exception(f"Unexpected error initializing MultiServerMCPClient (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    msg = f"Failed to connect to MCP servers after {max_retries} attempts: {e}"
                    raise RuntimeError(msg) from e

            # Exponential backoff
            await asyncio.sleep(base_delay * (2**attempt))

        if not client:
            msg = "Failed to create MCP client"
            raise RuntimeError(msg)

        try:
            yield client
        finally:
            # Clean up active subprocesses managed by the client if they exist
            # LangChain's MultiServerMCPClient manages connections in `client._connections`
            # or `client.connections` depending on version. We inspect and close them.
            try:
                connections = getattr(client, "connections", getattr(client, "_connections", {}))
                for server_name, connection in connections.items():
                    logger.debug(f"Attempting to close connection for {server_name}")
                    # Most connections have a close() or _close() method, or an underlying process
                    close_method = getattr(connection, "close", getattr(connection, "_close", None))
                    if close_method:
                        if asyncio.iscoroutinefunction(close_method):
                            await asyncio.wait_for(close_method(), timeout=2.0)
                        else:
                            close_method()
            except Exception as cleanup_err:
                logger.warning(f"Failed to cleanly shutdown MCP connections: {cleanup_err}")
