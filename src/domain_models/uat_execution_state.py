from pydantic import BaseModel, ConfigDict, Field

from .multimodal_artifact_schema import MultiModalArtifact


class UatExecutionState(BaseModel):
    """Execution state of dynamic UAT pipeline."""

    model_config = ConfigDict(extra="forbid")

    exit_code: int = Field(..., description="Integer exit code of the pytest execution.")
    stdout: str = Field(default="", description="Standard output from the test runner.")
    stderr: str = Field(default="", description="Standard error from the test runner.")
    artifacts: list[MultiModalArtifact] = Field(
        default_factory=list, description="Validated list of multi-modal artifacts generated."
    )
