from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

CycleStatus = Literal["planned", "in_progress", "review_fix", "completed", "failed"]


class UatAnalysis(BaseModel):
    """UAT execution analysis"""

    model_config = ConfigDict(extra="forbid")
    verdict: Literal["PASS", "FAIL"]
    summary: str
    behavior_analysis: str


class ConflictRegistryItem(BaseModel):
    """Tracks unresolved merge conflicts for an AI cycle."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(..., description="Path to the file with conflicts")
    conflict_markers: list[str] = Field(..., description="List of markers detected")
    resolution_attempts: int = Field(default=0, description="Number of attempts to resolve")
    resolved: bool = Field(default=False, description="Whether the conflict is resolved")


from typing import Any


class ToolExecutionErrorModel(BaseModel):
    """Encapsulates tool execution protocol errors."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    message: str = Field(..., description="The error message from the tool protocol")
    tool_name: str = Field(..., description="The name of the tool that failed")
    code: int = Field(default=-1, description="Protocol error code or internal code")


class ToolExecutionError(Exception):
    def __init__(self, message: str, tool_name: str, code: int = -1):
        self.data = ToolExecutionErrorModel(message=message, tool_name=tool_name, code=code)
        self.message = message
        self.tool_name = tool_name
        self.code = code
        super().__init__(message)


class E2BExecutionResult(BaseModel):
    """Artifacts from dynamic sandbox execution."""

    model_config = ConfigDict(extra="forbid")

    stdout: str = Field(default="", description="Standard output from test runner")
    stderr: str = Field(default="", description="Standard error from test runner")
    exit_code: int = Field(..., description="Exit code from execution, 0 means pass")
    coverage_report: str | None = Field(default=None, description="Coverage report output")
