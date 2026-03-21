import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from langchain_mcp_adapters.client import MultiServerMCPClient

from src.mcp_router.schemas import E2bMcpConfig, GitHubMcpConfig


class McpClientManager:
    """Manages the lifecycle of MCP clients."""

    # Explicitly whitelist safe prefixes for system and common development vars, including API keys that might be necessary.
    SAFE_ENV_KEY_PREFIXES: tuple[str, ...] = (
        "PATH", "USER", "HOME", "LANG", "LC_", "TERM", "TZ",
        "PYTHON", "LD_", "VIRTUAL_ENV", "NODE_", "NVM_", "NPM_", "BUN_",
        "AC_CDD_", "OPENAI_", "ANTHROPIC_", "JULES_", "E2B_", "OPENROUTER_", "GEMINI_",
        "GITHUB_PERSONAL_ACCESS_TOKEN" # Added explicitly in get_connection_config anyway
    )

    # Strictly reject known extremely dangerous execution prefixes
    DANGEROUS_ENV_KEY_PREFIXES: tuple[str, ...] = (
        "SUDO_", "SSH_", "AWS_SECRET_ACCESS_KEY", "GCP_PRIVATE_KEY"
    )

    @classmethod
    def _sanitize_environment(cls) -> dict[str, str]:
        """
        Sanitizes the environment dictionary to prevent leakage of secrets.
        Uses a whitelist approach prioritizing known safe development prefixes and rejecting extremely dangerous ones.
        Value-based scanning is removed because standard API keys/tokens are required for child processes.
        """
        sanitized = {}

        for key, value in os.environ.items():
            # Strictly blacklist known very dangerous keys
            if any(key.upper().startswith(danger) for danger in cls.DANGEROUS_ENV_KEY_PREFIXES):
                continue

            # Allow keys that match our safe prefixes
            if any(key.upper().startswith(safe) for safe in cls.SAFE_ENV_KEY_PREFIXES):
                sanitized[key] = value

        return sanitized

    @asynccontextmanager
    async def get_client(self) -> AsyncGenerator[MultiServerMCPClient, None]:  # noqa: C901
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

        max_retries = 3
        base_delay = 1.0

        client = None
        for attempt in range(max_retries):
            try:
                # MultiServerMCPClient init is synchronous, so we run it in a separate thread to avoid blocking the event loop
                client = await asyncio.to_thread(MultiServerMCPClient, connection_config)

                # Check if it exposes an explicit connect method to verify it actually works
                if hasattr(client, "connect_all") and callable(client.connect_all):
                    await asyncio.wait_for(client.connect_all(), timeout=15.0)

                break
            except Exception:
                logger.exception(f"Error initializing MCP Client (attempt {attempt + 1}/{max_retries}).")
                if attempt == max_retries - 1:
                    msg = f"Failed to connect to MCP servers after {max_retries} attempts. Initialization aborted safely."
                    raise RuntimeError(msg) from None

            # Exponential backoff
            await asyncio.sleep(base_delay * (2**attempt))

        if not client:
            msg = "Failed to create MCP client"
            raise RuntimeError(msg)

        try:
            yield client
        finally:
            try:
                # Clean up MCP subprocesses and sessions effectively
                if hasattr(client, "close") and callable(client.close):
                    await asyncio.wait_for(client.close(), timeout=5.0)
                elif hasattr(client, "disconnect_all") and callable(client.disconnect_all):
                    await asyncio.wait_for(client.disconnect_all(), timeout=5.0)
            except Exception as e:
                logger.debug(f"Error during MCP Client Teardown: {e}")
