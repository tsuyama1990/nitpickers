from pydantic import BaseModel, ConfigDict, Field


class DispatcherConfig(BaseModel):
    """Configuration for the async dispatcher."""

    model_config = ConfigDict(extra="forbid")

    max_concurrent_tasks: int = Field(
        default=10, ge=1, description="Maximum number of concurrent tasks"
    )
    retry_backoff_factor: float = Field(
        default=2.0, gt=0, description="Backoff factor for retry on 429"
    )
    max_retries: int = Field(
        default=5, ge=0, description="Maximum number of retries for API requests"
    )
