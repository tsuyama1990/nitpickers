from pydantic import BaseModel, ConfigDict


class MarkdownTestBlock(BaseModel):
    execution_language: str
    scenario_id: str
    code_payload: str

    model_config = ConfigDict(extra="forbid")
