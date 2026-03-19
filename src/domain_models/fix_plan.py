from pydantic import BaseModel, ConfigDict, Field


class FileModification(BaseModel):
    filepath: str = Field(...)
    explanation: str = Field(...)
    diff_block: str = Field(...)

    model_config = ConfigDict(strict=True)


class FixPlan(BaseModel):
    modifications: list[FileModification] = Field(...)

    model_config = ConfigDict(strict=True)
