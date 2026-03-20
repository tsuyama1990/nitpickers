from pydantic import BaseModel, ConfigDict, Field, field_validator


class UATResult(BaseModel):
    exit_code: int = Field(...)
    stderr: str = Field(...)
    screenshot_path: str | None = Field(default=None)
    dom_trace_path: str | None = Field(default=None)
    console_logs: str | None = Field(default=None)

    @field_validator("screenshot_path", "dom_trace_path", "console_logs", mode="before")
    @classmethod
    def validate_path_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            msg = "Path cannot be empty if provided"
            raise ValueError(msg)
        return v

    model_config = ConfigDict(strict=True, extra="forbid")
