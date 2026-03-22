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
    base_content: str | None = Field(default=None, description="Code from common ancestor")
    local_content: str | None = Field(default=None, description="Code from local branch")
    remote_content: str | None = Field(default=None, description="Code from remote branch")


class ConflictResolutionSchema(BaseModel):
    """
    Schema for the Master Integrator LLM to return properly resolved file content.
    This guarantees output is consistently provided as a JSON block, bypassing
    brittle markdown-scraping mechanisms, avoiding Git marker insertion.
    """

    model_config = ConfigDict(extra="forbid")

    resolved_code: str = Field(
        ...,
        description="The fully resolved file content, entirely free of Git conflict markers (`<<<<<<<`)",
    )


class E2BExecutionResult(BaseModel):
    """Artifacts from dynamic sandbox execution."""

    model_config = ConfigDict(extra="forbid")

    stdout: str = Field(default="", description="Standard output from test runner")
    stderr: str = Field(default="", description="Standard error from test runner")
    exit_code: int = Field(..., description="Exit code from execution, 0 means pass")
    coverage_report: str | None = Field(default=None, description="Coverage report output")
