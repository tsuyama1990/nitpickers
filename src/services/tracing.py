import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from langchain_core.tracers.context import tracing_v2_enabled

from src.domain_models.tracing import LangSmithConfig, TracingMetadata
from src.utils import logger


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

    @contextmanager
    def trace_context(self, project_name: str | None = None) -> Iterator[None]:
        """Context manager for tracing with dynamic project routing."""
        if not self.is_enabled:
            yield
            return

        api_key = self.config.api_key or os.environ.get("LANGCHAIN_API_KEY")
        if not api_key:
            logger.warning(
                "LangSmith tracing enabled but no API key provided. "
                "Tracing will be ignored to prevent crashes."
            )
            # Temporarily disable tracing to avoid crashes
            original_val = os.environ.get("LANGCHAIN_TRACING_V2")
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            try:
                yield
            finally:
                if original_val is not None:
                    os.environ["LANGCHAIN_TRACING_V2"] = original_val
                else:
                    del os.environ["LANGCHAIN_TRACING_V2"]
            return

        target_project = (
            project_name
            or self.config.project_name
            or os.environ.get("LANGCHAIN_PROJECT", "nitpickers-default")
        )

        with tracing_v2_enabled(project_name=target_project):
            yield
