from pydantic import BaseModel, ConfigDict, Field


class UXViolation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    principle: str = Field(..., description="The UI/UX principle that was violated.")
    element: str = Field(..., description="The specific UI element causing the violation.")
    issue: str = Field(..., description="Description of the UX issue.")
    suggestion: str = Field(..., description="Actionable suggestion to fix the issue.")


class UXAuditReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    overall_score: int = Field(..., description="Overall UX score out of 100.")
    good_points: list[str] = Field(
        default_factory=list, description="List of principles successfully applied."
    )
    violations: list[UXViolation] = Field(
        default_factory=list, description="List of UX violations found."
    )
