import os
from typing import Any

from src.domain_models.tracing import LangSmithConfig, TracingMetadata


class TracingService:
    """Service to manage LangSmith tracing."""

    def __init__(self, config: LangSmithConfig) -> None:
        self.config = config

    @property
    def is_enabled(self) -> bool:
        # Check environment variable if config override is not set or false
        env_enabled = os.environ.get("LANGCHAIN_TRACING_V2", "false").lower() == "true"
        return self.config.tracing_enabled or env_enabled

    def get_run_config(self, metadata: TracingMetadata) -> dict[str, Any]:
        """Get RunnableConfig compatible kwargs for LangGraph."""
        return metadata.to_langchain_kwargs()
