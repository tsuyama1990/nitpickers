from pydantic import BaseModel, ConfigDict, Field, SecretStr


class McpServerConfig(BaseModel):
    """Configuration for the MCP Server."""

    model_config = ConfigDict(extra="forbid")

    e2b_api_key: SecretStr = Field(..., description="API key for the E2B Sandbox")
    timeout_seconds: int = Field(default=300, ge=1, description="Timeout for MCP server operations")
    npx_path: str = Field(default="npx", description="Path to the npx executable")


class DispatcherConfig(BaseModel):
    """Configuration for the async dispatcher."""

    model_config = ConfigDict(extra="forbid")

    max_concurrent_tasks: int = Field(
        default=6, ge=1, description="Maximum number of concurrent tasks"
    )
    retry_backoff_factor: float = Field(
        default=2.0, gt=0, description="Backoff factor for retry on 429"
    )
    max_retries: int = Field(
        default=5, ge=0, description="Maximum number of retries for API requests"
    )
