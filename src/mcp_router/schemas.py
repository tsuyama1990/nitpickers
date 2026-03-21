import re
from typing import Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class JulesMcpConfig(BaseSettings):
    """Configuration for the Jules MCP server connection."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    JULES_API_KEY: SecretStr = Field(
        ...,
        min_length=10,
        description="Jules API key for authentication",
    )
    JULES_COMMAND: str = Field("npx", description="The command to boot the Jules server")
    JULES_ARGS: list[str] = Field(["-y", "@google/jules-mcp"], description="Arguments for the Jules server command")

    @field_validator("JULES_API_KEY", mode="before")
    @classmethod
    def validate_api_key(cls, v: str | SecretStr) -> SecretStr | str:
        val = v.get_secret_value() if isinstance(v, SecretStr) else v
        if not val or not str(val).strip():
            msg = "JULES_API_KEY cannot be empty"
            raise ValueError(msg)
        # Pre-validate key format matches a valid identifier structure (e.g. alphanumeric with symbols)
        if not re.match(r"^[\w.-]+$", str(val)):
            msg = "JULES_API_KEY format is invalid"
            raise ValueError(msg)
        return v

    def get_connection_config(self, base_env: dict[str, str] | None = None) -> dict[str, Any]:
        """Get the dynamic dictionary connection config for MultiServerMCPClient."""
        env = dict(base_env or {})

        # Verify presence in OS env as a fallback safety measure if needed, but primary is the SecretStr
        if not self.JULES_API_KEY.get_secret_value():
            msg = "JULES_API_KEY is not configured properly."
            raise ValueError(msg)

        env["JULES_API_KEY"] = self.JULES_API_KEY.get_secret_value()

        return {
            "jules": {
                "command": self.JULES_COMMAND,
                "args": self.JULES_ARGS,
                "env": env,
                "transport": "stdio",
            }
        }


class E2bMcpConfig(BaseSettings):
    """Configuration for the E2B MCP server connection."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    E2B_API_KEY: SecretStr = Field(
        ...,
        min_length=10,
        description="E2B API key for authentication",
    )
    E2B_COMMAND: str = Field("npx", description="The command to boot the E2B server")
    E2B_ARGS: list[str] = Field(["-y", "@e2b/mcp-server"], description="Arguments for the E2B server command")

    @field_validator("E2B_API_KEY", mode="before")
    @classmethod
    def validate_api_key(cls, v: str | SecretStr) -> SecretStr | str:
        val = v.get_secret_value() if isinstance(v, SecretStr) else v
        if not val or not str(val).strip():
            msg = "E2B_API_KEY cannot be empty"
            raise ValueError(msg)
        return v

    def get_connection_config(self, base_env: dict[str, str] | None = None) -> dict[str, Any]:
        """Get the dynamic dictionary connection config for MultiServerMCPClient."""
        env = dict(base_env or {})

        if not self.E2B_API_KEY.get_secret_value():
            msg = "E2B_API_KEY is not configured properly."
            raise ValueError(msg)

        env["E2B_API_KEY"] = self.E2B_API_KEY.get_secret_value()

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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    GITHUB_PERSONAL_ACCESS_TOKEN: SecretStr = Field(
        ...,
        min_length=10,
        description="GitHub Personal Access Token for authentication",
    )
    GITHUB_COMMAND: str = Field("npx", description="The command to boot the GitHub server")
    GITHUB_ARGS: list[str] = Field(["-y", "@modelcontextprotocol/server-github"], description="Arguments for the GitHub server command")

    @field_validator("GITHUB_PERSONAL_ACCESS_TOKEN", mode="before")
    @classmethod
    def validate_github_token(cls, v: str | SecretStr) -> SecretStr | str:
        val = v.get_secret_value() if isinstance(v, SecretStr) else v
        if not val or not str(val).strip():
            msg = "GITHUB_PERSONAL_ACCESS_TOKEN cannot be empty"
            raise ValueError(msg)
        return v

    def get_connection_config(self, base_env: dict[str, str] | None = None) -> dict[str, Any]:
        """Get the dynamic dictionary connection config for MultiServerMCPClient."""
        env = dict(base_env or {})

        if not self.GITHUB_PERSONAL_ACCESS_TOKEN.get_secret_value():
            msg = "GITHUB_PERSONAL_ACCESS_TOKEN is not configured properly."
            raise ValueError(msg)

        env["GITHUB_PERSONAL_ACCESS_TOKEN"] = self.GITHUB_PERSONAL_ACCESS_TOKEN.get_secret_value()

        return {
            "github": {
                "command": self.GITHUB_COMMAND,
                "args": self.GITHUB_ARGS,
                "env": env,
                "transport": "stdio",
            }
        }
