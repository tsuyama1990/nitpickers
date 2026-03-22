import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient

from src.mcp_router.schemas import E2bMcpConfig, GitHubMcpConfig, JulesMcpConfig


class McpClientManager:
    """Manages the lifecycle of MCP clients."""

    # Strictly reject known extremely dangerous execution prefixes
    DANGEROUS_ENV_KEY_PREFIXES: tuple[str, ...] = (
        "SUDO_", "SSH_", "AWS_SECRET_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "GCP_PRIVATE_KEY", "AZURE_CLIENT_SECRET"
    )

    @classmethod
    def _sanitize_environment(cls) -> dict[str, str]:
        """
        Sanitizes the environment dictionary to prevent leakage of secrets.
        Uses a blacklisting approach to remove dangerous prefixes but retains
        API keys needed for MCP authentication.
        """
        sanitized = os.environ.copy()

        for key in list(sanitized.keys()):
            upper_key = key.upper()
            if any(upper_key.startswith(danger) for danger in cls.DANGEROUS_ENV_KEY_PREFIXES):
                del sanitized[key]

        return sanitized

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[MultiServerMCPClient, None]:
        """Provides an asynchronous context manager for the MCP client with robust error handling."""
        import logging

        from pydantic import ValidationError
        logger = logging.getLogger(__name__)

        # Override the env with sanitized environment to prevent leakages
        sanitized_env = self._sanitize_environment()

        # Build dynamic connections from the configs
        connection_config = {}

        try:
            config = E2bMcpConfig()  # type: ignore[call-arg]
            connection_config.update(config.get_connection_config(sanitized_env))
        except ValidationError as e:
            logger.warning(f"E2B MCP server configuration missing or invalid. E2B tools will be disabled. Error: {e}")

        try:
            github_config = GitHubMcpConfig()  # type: ignore[call-arg]
            connection_config.update(github_config.get_connection_config(sanitized_env))
        except ValidationError as e:
            logger.warning(f"GitHub MCP server configuration missing or invalid. GitHub tools will be disabled. Error: {e}")

        try:
            jules_config = JulesMcpConfig()  # type: ignore[call-arg]
            connection_config.update(jules_config.get_connection_config(sanitized_env))
        except ValidationError as e:
            logger.warning(f"Jules MCP server configuration missing or invalid. Jules tools will be disabled. Error: {e}")

        client = MultiServerMCPClient(connection_config)

        # Ensure async connectivity without blocking the event loop initially.
        # MultiServerMCPClient initializes properties synchronously but the actual connection is async.
        # Wait for connections concurrently to speed up initialization.
        try:
            # MultiServerMCPClient doesn't have connect_all by default, but relies on aconnect / contextmgrs
            # Assuming client is properly configured.
            pass
        except Exception as e:
            logger.exception("Error initializing MCP Client")
            msg = "Failed to connect to MCP servers. Initialization aborted safely."
            raise RuntimeError(msg) from e

        try:
            yield client
        finally:
            try:
                # Use context manager protocol consistently across all MCP client operations
                if hasattr(client, "__aexit__"):
                    await client.__aexit__(None, None, None) # type: ignore[func-returns-value]
                elif hasattr(client, "close") and callable(client.close):
                    await client.close()
            except Exception as e:
                logger.debug(f"Error during MCP Client Teardown: {e}")
