from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CriticFeedbackItem(BaseModel):
    """Specific feedback from the architect critic."""
    model_config = ConfigDict(extra="forbid")

    category: Literal[
        "N+1 Problem",
        "Race Condition",
        "Scalability Bottleneck",
        "Security Risk",
        "Interface Contract Missing",
        "Other",
    ] = Field(description="Category of the architectural issue")
    severity: Literal["fatal", "warning"] = Field(
        description="'fatal' MUST be used if an interface contract is missing or there is a major architectural flaw."
    )
    issue_description: str = Field(description="Clear and concise description of the issue")
    concrete_fix: str = Field(description="Specific structural change required")


class CriticResponse(BaseModel):
    """Response from the architect critic evaluating the specifications."""
    model_config = ConfigDict(extra="forbid")

    is_passed: bool = Field(description="True ONLY if there are zero fatal issues.")
    summary: str = Field(description="Brief summary of the evaluation.")
    feedback: list[CriticFeedbackItem] = Field(
        default_factory=list,
        description="List of specific issues found in the architecture.",
    )
