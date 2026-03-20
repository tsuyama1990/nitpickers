from pydantic import BaseModel, ConfigDict, Field


class FixPlanSchema(BaseModel):
    """
    Structured JSON Fix Plan returned by the Stateless Auditor to the Worker.
    Represents an authoritative, unyielding contract for bug remediation.
    """

    model_config = ConfigDict(extra="forbid")

    target_file: str = Field(
        ...,
        description="The exact path of the file to modify to resolve the bug."
    )
    defect_description: str = Field(
        ...,
        description="A clear reasoning and explanation of the defect and the intended fix."
    )
    git_diff_patch: str = Field(
        ...,
        description="A precise structural modification instruction block, such as code snippets or a diff."
    )
