from pydantic import BaseModel, ConfigDict, field_validator


class UATResult(BaseModel):
    exit_code: int
    stderr: str
    screenshot_path: str | None = None
    dom_trace_path: str | None = None
    console_logs: str | None = None

    @field_validator("screenshot_path", "dom_trace_path", "console_logs", mode="before")
    @classmethod
    def validate_path_not_empty(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            msg = "Path cannot be empty if provided"
            raise ValueError(msg)
        return v

    model_config = ConfigDict(extra="forbid")
