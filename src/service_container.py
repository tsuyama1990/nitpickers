from dataclasses import dataclass

from services.artifacts import ArtifactManager
from services.contracts import ContractManager
from services.file_ops import FilePatcher
from services.git_ops import GitManager
from services.jules_client import JulesClient
from services.llm_reviewer import LLMReviewer


@dataclass
class ServiceContainer:
    file_patcher: FilePatcher
    contract_manager: ContractManager
    artifact_manager: ArtifactManager
    jules: JulesClient | None = None
    reviewer: LLMReviewer | None = None
    git: GitManager | None = None

    @classmethod
    def default(cls) -> "ServiceContainer":
        return cls(
            file_patcher=FilePatcher(),
            contract_manager=ContractManager(),
            artifact_manager=ArtifactManager(),
            jules=JulesClient(),
            reviewer=LLMReviewer(),
            git=GitManager(),
        )
