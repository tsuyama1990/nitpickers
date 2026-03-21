from pydantic import BaseModel, ConfigDict, Field, field_validator


class McpServerConfig(BaseModel):
    """Configuration for initializing an MCP server."""

    model_config = ConfigDict(extra="forbid")

    server_name: str = Field(..., description="Name of the MCP server, e.g., 'e2b'")
    command: str = Field(default="npx", description="Path or command to execute the server")
    args: list[str] = Field(..., description="Arguments to pass to the command")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables for the server")
    timeout_seconds: int = Field(default=30, ge=1, description="Timeout for connection in seconds")

    @field_validator("env")
    @classmethod
    def validate_env(cls, v: dict[str, str]) -> dict[str, str]:
        # Validate that necessary keys are not empty strings or whitespace
        for key, value in v.items():
            if not value.strip():
                msg = f"Environment variable {key} cannot be empty"
                raise ValueError(msg)
        return v

class ToolExecutionError(BaseModel):
    """Error returned when a tool execution fails."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., description="Error message from the MCP server or client")
    tool_name: str = Field(..., description="Name of the tool that failed")
    code: int = Field(default=-1, description="Error code or exit code")
