from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class E2bMcpConfig(BaseSettings):
    """Configuration for the E2B MCP server connection."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", env_ignore_empty=True)

    E2B_API_KEY: str = Field(
        ...,
        min_length=10,
        description="E2B API key for authentication",
    )
    E2B_COMMAND: str = Field("npx", description="The command to boot the E2B server")
    E2B_ARGS: list[str] = Field(["-y", "@e2b/mcp-server"], description="Arguments for the E2B server command")

    def get_connection_config(self, base_env: dict[str, str] | None = None) -> dict[str, Any]:
        """Get the dynamic dictionary connection config for MultiServerMCPClient."""
        env = dict(base_env or {})
        env["E2B_API_KEY"] = self.E2B_API_KEY

        return {
            "e2b": {
                "command": self.E2B_COMMAND,
                "args": self.E2B_ARGS,
                "env": env,
                "transport": "stdio",
            }
        }


class GitHubMcpConfig(BaseSettings):
    """Configuration for the GitHub MCP server connection."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", env_ignore_empty=True)

    GITHUB_PERSONAL_ACCESS_TOKEN: str = Field(
        ...,
        min_length=10,
        description="GitHub Personal Access Token",
    )
    GITHUB_COMMAND: str = Field("npx", description="The command to boot the GitHub server")
    GITHUB_ARGS: list[str] = Field(
        ["-y", "@modelcontextprotocol/server-github"],
        description="Arguments for the GitHub server command",
    )

    def get_connection_config(self, base_env: dict[str, str] | None = None) -> dict[str, Any]:
        """Get the dynamic dictionary connection config for MultiServerMCPClient."""
        env = dict(base_env or {})
        env["GITHUB_PERSONAL_ACCESS_TOKEN"] = self.GITHUB_PERSONAL_ACCESS_TOKEN

        return {
            "github": {
                "command": self.GITHUB_COMMAND,
                "args": self.GITHUB_ARGS,
                "env": env,
                "transport": "stdio",
            }
        }
