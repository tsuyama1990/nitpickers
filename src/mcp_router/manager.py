import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from src.mcp_router.schemas import E2bMcpConfig, GitHubMcpConfig


class McpClientManager:
    """Manages the lifecycle of MCP clients."""

    SAFE_ENV_KEYS: tuple[str, ...] = (
        "PATH", "USER", "HOME", "LANG", "LC_ALL", "TERM", "TZ",
        "PYTHONPATH", "LD_LIBRARY_PATH", "VIRTUAL_ENV",
        "NODE_ENV", "NVM_DIR", "NVM_BIN", "NVM_INC", "NPM_CONFIG_PREFIX"
    )

    _VALUE_SECRET_PATTERNS = None

    @classmethod
    def _get_secret_pattern(cls) -> Any:
        if cls._VALUE_SECRET_PATTERNS is None:
            import re
            cls._VALUE_SECRET_PATTERNS = re.compile(
                r"(eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}|"  # JWT
                r"sk-[A-Za-z0-9]{20,}|"                         # OpenAI/similar keys
                r"ghp_[A-Za-z0-9]{36}|"                         # GitHub classic PAT
                r"e2b_[a-zA-Z0-9_]+)",                          # E2B Keys
                re.IGNORECASE
            )
        return cls._VALUE_SECRET_PATTERNS

    @classmethod
    def _sanitize_environment(cls) -> dict[str, str]:
        """
        Sanitizes the environment dictionary to prevent leakage of secrets.
        Uses a strict whitelist approach for allowed environment keys as requested.
        Additionally checks values for potential credential patterns.
        """
        sanitized = {}
        pattern = cls._get_secret_pattern()

        for key, value in os.environ.items():
            # Apply explicit whitelist constraint requested by auditor
            if key not in cls.SAFE_ENV_KEYS:
                continue
            # Apply value sanitization
            if pattern.search(value):
                continue
            sanitized[key] = value

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

        max_retries = 3
        base_delay = 1.0

        client = None
        for attempt in range(max_retries):
            try:
                # Add timeout to client initialization itself if possible or wait_for
                # Note: MultiServerMCPClient init is synchronous, but we'll wrap it safely
                client = MultiServerMCPClient(connection_config)
                break
            except Exception:
                logger.exception(f"Error initializing MCP Client (attempt {attempt + 1}/{max_retries}). Sensitive kwargs omitted.")
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
            # MultiServerMCPClient from langchain-mcp-adapters delegates cleanup natively
            # to context managers of its internal `session` methods. Reflection-based
            # teardown is unsafe against library updates.
            pass
