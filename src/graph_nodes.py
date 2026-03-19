from typing import Any

from rich.console import Console

from src.interfaces import IGraphNodes
from src.nodes import (
    ArchitectCriticNodes,
    ArchitectNodes,
    AuditorNodes,
    CoderCriticNodes,
    CoderNodes,
    CommitteeNodes,
    QaNodes,
    UatNodes,
    check_audit_outcome,
    check_coder_outcome,
    route_architect_critic,
    route_coder_critic,
    route_committee,
    route_qa,
    route_uat,
)
from src.nodes.coder_critic import CoderCriticNodes
from src.nodes.global_refactor import GlobalRefactorNodes
from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
from src.sandbox import SandboxRunner
from src.services.audit_orchestrator import AuditOrchestrator
from src.services.git_ops import GitManager
from src.services.jules_client import JulesClient
from src.services.llm_reviewer import LLMReviewer
from src.state import CycleState

console = Console()


class CycleNodes(IGraphNodes):
    """
    Encapsulates the logic for each node in the AC-CDD workflow graph.
    """

    def __init__(self, sandbox_runner: SandboxRunner, jules_client: JulesClient) -> None:
        self.sandbox = sandbox_runner
        self.jules = jules_client

        from src.service_container import ServiceContainer

        container = ServiceContainer.default()

        self.git = (
            container.resolve("git_manager") if hasattr(container, "resolve") else GitManager()
        )
        self.llm_reviewer = LLMReviewer(sandbox_runner=sandbox_runner)
        self.audit_orchestrator = AuditOrchestrator(jules_client, sandbox_runner)

        self._architect = ArchitectNodes(self.jules, self.git)
        self._architect_critic = ArchitectCriticNodes(self.jules)
        self._coder = CoderNodes(self.jules)
        self._coder_critic = CoderCriticNodes(self.jules)
        self._auditor = AuditorNodes(self.jules, self.git, self.llm_reviewer)
        self._committee = CommitteeNodes()
        self._uat = UatNodes(self.git)
        self._sandbox_evaluator = SandboxEvaluatorNodes()
        self._qa = QaNodes(self.jules, self.git, self.llm_reviewer)
        self._coder_critic = CoderCriticNodes(self.jules)

        # Dependency injection for Global Refactor
        from src.services.refactor_usecase import RefactorUsecase

        if hasattr(container, "resolve"):
            refactor_usecase = container.resolve(RefactorUsecase)
        else:
            refactor_usecase = RefactorUsecase(jules_client=self.jules)

        self._global_refactor = GlobalRefactorNodes(usecase=refactor_usecase)

    async def architect_session_node(self, state: CycleState) -> dict[str, Any]:
        return await self._architect.architect_session_node(state)

    async def architect_critic_node(self, state: CycleState) -> dict[str, Any]:
        return await self._architect_critic.architect_critic_node(state)

    async def _send_audit_feedback_to_session(
        self, session_id: str, feedback: str
    ) -> dict[str, Any] | None:
        return await self._architect.send_audit_feedback_to_session(session_id, feedback)

    async def coder_session_node(self, state: CycleState) -> dict[str, Any]:
        return await self._coder.coder_session_node(state)

    async def auditor_node(self, state: CycleState) -> dict[str, Any]:
        return await self._auditor.auditor_node(state)

    async def committee_manager_node(self, state: CycleState) -> dict[str, Any]:
        return await self._committee.committee_manager_node(state)

    async def coder_critic_node(self, state: CycleState) -> dict[str, Any]:
        return await self._coder_critic.coder_critic_node(state)

    async def uat_evaluate_node(self, state: CycleState) -> dict[str, Any]:
        return await self._uat.uat_evaluate_node(state)

    async def sandbox_evaluate_node(self, state: CycleState) -> dict[str, Any]:
        return await self._sandbox_evaluator.sandbox_evaluate_node(state)

    async def coder_critic_node(self, state: CycleState) -> dict[str, Any]:
        return await self._coder_critic.coder_critic_node(state)

    async def global_refactor_node(self, state: CycleState) -> dict[str, Any]:
        return await self._global_refactor.global_refactor_node(state)

    def check_coder_outcome(self, state: CycleState) -> str:
        return check_coder_outcome(state)

    def check_audit_outcome(self, _state: CycleState) -> str:
        return check_audit_outcome(_state)

    def route_architect_critic(self, state: CycleState) -> str:
        return route_architect_critic(state)

    def route_committee(self, state: CycleState) -> str:
        return route_committee(state)

    def route_coder_critic(self, state: CycleState) -> str:
        return route_coder_critic(state)

    def route_uat(self, state: CycleState) -> str:
        return route_uat(state)

    def route_coder_critic(self, state: CycleState) -> str:
        return route_coder_critic(state)

    async def qa_session_node(self, state: CycleState) -> dict[str, Any]:
        return await self._qa.qa_session_node(state)

    async def qa_auditor_node(self, state: CycleState) -> dict[str, Any]:
        return await self._qa.qa_auditor_node(state)

    def route_qa(self, state: CycleState) -> str:
        return route_qa(state)
