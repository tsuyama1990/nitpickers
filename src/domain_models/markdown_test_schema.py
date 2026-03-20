from pydantic import BaseModel, ConfigDict


class MarkdownTestBlock(BaseModel):
    """
    Represents an executable code block extracted from a Markdown specification file
    (e.g., ALL_SPEC.md). This schema acts as the strict contract between static
    documentation and the Pytest dynamic execution environment, ensuring that only
    well-formed scenarios are evaluated during the Docs-as-Tests pipeline.
    """

    execution_language: str
    scenario_id: str
    code_payload: str

    model_config = ConfigDict(extra="forbid")
