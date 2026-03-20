from pathlib import Path

from pydantic import BaseModel, ConfigDict, model_validator


class MultiModalArtifact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_id: str
    screenshot_path: str
    trace_path: str | None = None
    console_logs: list[str]
    traceback: str

    @model_validator(mode="after")
    def _verify_file_paths(self) -> "MultiModalArtifact":
        """Verify that the paths for screenshot and trace exist."""
        if not Path(self.screenshot_path).exists():
            msg = f"Screenshot file not found: {self.screenshot_path}"
            raise ValueError(msg)
        if self.trace_path is not None and not Path(self.trace_path).exists():
            msg = f"Trace file not found: {self.trace_path}"
            raise ValueError(msg)
        return self
