from dataclasses import dataclass
from typing import Any

from src.services.artifacts import ArtifactManager
from src.services.contracts import ContractManager
from src.services.file_ops import FilePatcher
from src.services.llm_reviewer import LLMReviewer


@dataclass
class ServiceContainer:
    file_patcher: FilePatcher
    contract_manager: ContractManager
    artifact_manager: ArtifactManager
    jules: Any | None = None
    reviewer: LLMReviewer | None = None
    git: Any | None = None

    @classmethod
    def default(cls) -> "ServiceContainer":
        return cls(
            file_patcher=FilePatcher(),
            contract_manager=ContractManager(),
            artifact_manager=ArtifactManager(),
            jules=None,
            reviewer=LLMReviewer(),
            git=None,
        )
