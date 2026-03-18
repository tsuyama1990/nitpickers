from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .file_ops import FileArtifact


class CyclePlan(BaseModel):
    """Planning phase artifacts"""

    model_config = ConfigDict(extra="forbid")
    spec_file: FileArtifact
    schema_file: FileArtifact
    uat_file: FileArtifact
    thought_process: str = Field(..., description="Thought process behind the design")


class Feature(BaseModel):
    name: str
    description: str
    priority: Literal["High", "Medium", "Low"]
    acceptance_criteria: list[str]


class TechnicalConstraint(BaseModel):
    category: str
    description: str


class StructuredSpec(BaseModel):
    """Structured representation of ALL_SPEC.md"""

    project_name: str
    version: str = "1.0.0"
    overview: str = Field(..., description="Executive summary of the project")
    goals: list[str] = Field(..., description="Primary business/learning goals")
    architecture_overview: str = Field(..., description="High-level system design")
    features: list[Feature] = Field(..., description="Initial backlog of features")
    constraints: list[TechnicalConstraint] = Field(default_factory=list)
    terminology: dict[str, str] = Field(default_factory=dict, description="Domain glossary")
