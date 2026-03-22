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
    check_coder_outcome,
    route_architect_critic,
    route_auditor,
    route_final_critic,
    route_qa,
    route_sandbox_evaluate,
)
from src.nodes.global_refactor import GlobalRefactorNodes
from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
from src.sandbox import SandboxRunner
from src.services.audit_orchestrator import AuditOrchestrator
from src.services.git_ops import GitManager
from src.services.jules_client import JulesClient
from src.services.llm_reviewer import LLMReviewer
from src.state import CycleState, IntegrationState

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

    async def uat_evaluate_node(self, state: CycleState) -> dict[str, Any]:
        return await self._uat.uat_evaluate_node(state)

    async def sandbox_evaluate_node(self, state: CycleState) -> dict[str, Any]:
        return await self._sandbox_evaluator.sandbox_evaluate_node(state)

    async def global_refactor_node(self, state: CycleState) -> dict[str, Any]:
        return await self._global_refactor.global_refactor_node(state)

    async def refactor_node(self, state: CycleState) -> dict[str, Any]:
        return await self.global_refactor_node(state)

    async def self_critic_node(self, state: CycleState) -> dict[str, Any]:
        return await self._coder_critic.coder_critic_node(state)

    async def final_critic_node(self, state: CycleState) -> dict[str, Any]:
        return await self._coder_critic.coder_critic_node(state)

    async def git_merge_node(self, state: "IntegrationState") -> dict[str, Any]:
        from pathlib import Path

        from src.services.conflict_manager import ConflictManager
        from src.services.git_ops import GitManager
        from src.utils import logger

        # We assume `state` includes fields like pr_url or unresolved_conflicts from IntegrationState
        try:
            if hasattr(state, "unresolved_conflicts") and state.unresolved_conflicts:
                logger.info("Found unresolved conflicts. Routing to Master Integrator.")
                return {"conflict_status": "conflict_detected"}

            # If pr_url is passed somehow, merge it; otherwise assume integration is handled locally
            pr_url = getattr(state, "pr_url", None)
            if pr_url:
                # Extract PR number from URL (e.g. https://github.com/owner/repo/pull/1)
                pr_number = pr_url.split("/")[-1]
                gm = GitManager()
                await gm.merge_pr(pr_number)

            # Double check via scan_conflicts to make sure Git is clean
            cm = ConflictManager()
            repo_path = Path.cwd()
            conflicts = cm.scan_conflicts(repo_path)
            if conflicts:
                # Actually detected real git conflicts
                return {"unresolved_conflicts": conflicts, "conflict_status": "conflict_detected"}

        except Exception as e:
            logger.error(f"Git merge failed: {e}")
            return {"error": str(e), "conflict_status": "conflict_detected"}

        return {"conflict_status": "success"}

    async def master_integrator_node(self, state: "IntegrationState") -> dict[str, Any]:
        from src.nodes.master_integrator import MasterIntegratorNodes
        from src.services.jules_client import JulesClient

        integrator = MasterIntegratorNodes(jules_client=JulesClient())
        return await integrator.master_integrator_node(state)

    async def global_sandbox_node(self, state: "IntegrationState") -> dict[str, Any]:
        from pathlib import Path

        from src.config import settings
        from src.enums import FlowStatus
        from src.process_runner import ProcessRunner
        from src.utils import logger

        # Decouple from CycleState mock and run integration tests natively via ProcessRunner
        # testing the global repository state after integration.
        logger.info("Running global integration sandbox validation...")
        runner = ProcessRunner()
        cmd = settings.sandbox.test_cmd.split()

        stdout, stderr, exit_code, timeout = await runner.run_command(
            cmd, cwd=Path.cwd(), check=False
        )

        if exit_code != 0 or timeout:
            logger.error(f"Global sandbox failed with exit code {exit_code}")
            return {"status": FlowStatus.FAILED.value}

        logger.info("Global sandbox validation passed.")
        return {"status": FlowStatus.COMPLETED.value}

    def route_merge(self, state: "IntegrationState") -> str:
        # Properly check for git conflict detection mapping
        status = (
            getattr(state, "conflict_status", None)
            if hasattr(state, "conflict_status")
            else getattr(state, "get", lambda x, y: None)("conflict_status", None)
        )
        if status == "conflict_detected":
            return "conflict"
        return "success"

    def route_global_sandbox(self, state: "IntegrationState") -> str:
        from src.enums import FlowStatus

        status = (
            getattr(state, "status", None)
            if hasattr(state, "status")
            else getattr(state, "get", lambda x, y: None)("status", None)
        )
        # Sandbox evaluators return FlowStatus.FAILED if general linter/pytest failures occur
        if status in (FlowStatus.FAILED.value, FlowStatus.FAILED, "failed"):
            return "failed"
        return "pass"

    def check_coder_outcome(self, state: CycleState) -> str:
        return check_coder_outcome(state)

    def route_architect_critic(self, state: CycleState) -> str:
        return route_architect_critic(state)

    def route_auditor(self, state: CycleState) -> str:
        return route_auditor(state)

    def route_final_critic(self, state: CycleState) -> str:
        return route_final_critic(state)

    def route_sandbox_evaluate(self, state: CycleState) -> str:
        return route_sandbox_evaluate(state)

    async def qa_session_node(self, state: CycleState) -> dict[str, Any]:
        return await self._qa.qa_session_node(state)

    async def qa_auditor_node(self, state: CycleState) -> dict[str, Any]:
        return await self._qa.qa_auditor_node(state)

    def route_qa(self, state: CycleState) -> str:
        return route_qa(state)

    async def coder_critic_node(self, state: CycleState) -> dict[str, Any]:
        return await self._coder_critic.coder_critic_node(state)

    def route_coder_critic(self, state: CycleState) -> str:
        from src.nodes.routers import route_coder_critic

        return route_coder_critic(state)
