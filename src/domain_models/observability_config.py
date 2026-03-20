from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ObservabilityConfig(BaseModel):
    """
    Authoritative contract for the required observability environment variables.
    Enforces that LangSmith tracing is explicitly enabled and keys are present.
    """

    model_config = ConfigDict(extra="forbid")

    langchain_tracing_v2: str | bool = Field(
        ...,
        description="Must be 'true' or True to enable LangSmith tracing.",
    )
    langchain_api_key: str = Field(
        ...,
        min_length=1,
        description="LangSmith API Key.",
    )
    langchain_project: str = Field(
        ...,
        min_length=1,
        description="LangSmith Project Name.",
    )

    @field_validator("langchain_tracing_v2")
    @classmethod
    def validate_tracing_enabled(cls, v: Any) -> bool | str:
        if isinstance(v, str):
            if v.lower() != "true":
                msg = "LANGCHAIN_TRACING_V2 must be 'true'"
                raise ValueError(msg)
            return "true"
        if isinstance(v, bool):
            if not v:
                msg = "LANGCHAIN_TRACING_V2 must be True"
                raise ValueError(msg)
            return True
        msg = "LANGCHAIN_TRACING_V2 must be a boolean or 'true'"
        raise ValueError(msg)

    @field_validator("langchain_api_key", "langchain_project")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            msg = "Value cannot be empty or whitespace."
            raise ValueError(msg)
        return v
