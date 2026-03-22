from pydantic import BaseModel, ConfigDict, Field


class FilePatch(BaseModel):
    target_file: str = Field(..., description="The exact path of the file to modify.")
    git_diff_patch: str = Field(..., description="The code snippet or diff for this specific file.")


class FixPlanSchema(BaseModel):
    """
    Structured JSON Fix Plan returned by the Stateless Auditor to the Worker.
    Represents an authoritative, unyielding contract for bug remediation.
    """

    model_config = ConfigDict(extra="forbid")

    defect_description: str = Field(
        ..., description="A clear reasoning and explanation of the defect and the intended fix."
    )
    patches: list[FilePatch] = Field(
        ...,
        description="A list of files and their corresponding modifications required to resolve the bug.",
    )
