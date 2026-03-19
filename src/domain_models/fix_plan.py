from pydantic import BaseModel, ConfigDict


class FileModification(BaseModel):
    filepath: str
    explanation: str
    diff_block: str

    model_config = ConfigDict(strict=True)


class FixPlan(BaseModel):
    modifications: list[FileModification]

    model_config = ConfigDict(strict=True)
