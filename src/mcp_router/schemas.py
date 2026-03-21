from mcp import StdioServerParameters
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class E2bMcpConfig(BaseSettings):
    """Configuration for the E2B MCP server connection."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    E2B_API_KEY: str = Field(..., min_length=1, description="E2B API key for authentication")

    def get_stdio_parameters(self) -> StdioServerParameters:
        """Get the parameters to initialize the MCP client over stdio."""
        return StdioServerParameters(
            command="npx", args=["-y", "@e2b/mcp-server"], env={"E2B_API_KEY": self.E2B_API_KEY}
        )
