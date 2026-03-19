from pydantic import BaseModel, ConfigDict, Field


class GlobalRefactorResult(BaseModel):
    """
    Result of the global refactoring analysis and execution.
    """

    model_config = ConfigDict(extra="forbid")

    refactorings_applied: bool = Field(
        default=False,
        description="True if refactorings were applied, False otherwise.",
    )
    modified_files: list[str] = Field(
        default_factory=list,
        description="List of file paths that were modified during refactoring.",
    )
    summary: str = Field(
        default="",
        description="Summary of the refactorings applied or why none were needed.",
    )
