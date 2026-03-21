from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class E2bMcpConfig(BaseSettings):
    """Configuration for the E2B MCP server connection."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    E2B_API_KEY: str = Field(
        ...,
        min_length=10,
        pattern=r"^e2b_[a-zA-Z0-9_]+$",
        description="E2B API key for authentication (must start with e2b_)",
    )
    E2B_COMMAND: str = Field("npx", description="The command to boot the E2B server")
    E2B_ARGS: list[str] = Field(["-y", "@e2b/mcp-server"], description="Arguments for the E2B server command")

    def get_connection_config(self, base_env: dict[str, str] | None = None) -> dict[str, dict[str, str | list[str]]]:
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
