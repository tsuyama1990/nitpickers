from pydantic import BaseModel, ConfigDict, Field


class CriticResult(BaseModel):
    """Result of the Architect Self-Critic evaluation."""

    model_config = ConfigDict(extra="forbid")

    is_approved: bool = Field(
        description="Whether the architecture is approved without vulnerabilities."
    )
    vulnerabilities: list[str] = Field(
        default_factory=list, description="List of identified vulnerabilities or issues."
    )
    suggestions: list[str] = Field(
        default_factory=list, description="List of suggestions for improvement."
    )
