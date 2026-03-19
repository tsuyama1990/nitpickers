from typing import Any

from pydantic import BaseModel, Field


class LangSmithConfig(BaseModel):
    """Configuration for LangSmith tracing."""

    tracing_enabled: bool = Field(default=False, alias="LANGCHAIN_TRACING_V2")
    api_key: str | None = Field(default=None, alias="LANGCHAIN_API_KEY")
    project_name: str = Field(default="nitpickers-default", alias="LANGCHAIN_PROJECT")
    endpoint: str = Field(default="https://api.smith.langchain.com", alias="LANGCHAIN_ENDPOINT")


class TracingMetadata(BaseModel):
    """Standardized metadata payload attached to every LangSmith trace."""

    session_id: str = Field(description="The unique identifier for the current session/interaction")
    execution_type: str = Field(description="e.g., 'jules_session', 'batch_audit', 'cli_run'")
    git_branch: str | None = Field(default=None, description="The branch currently being analyzed")
    custom_metadata: dict[str, Any] = Field(default_factory=dict)

    def to_langchain_kwargs(self) -> dict[str, Any]:
        """Converts to kwargs suitable for graph.invoke(config=...)"""
        tags = [self.execution_type]
        if self.git_branch:
            tags.append(f"branch:{self.git_branch}")

        return {
            "run_name": f"Workflow_{self.execution_type.capitalize()}",
            "tags": tags,
            "metadata": {
                "session_id": self.session_id,
                **self.custom_metadata,
            },
        }
