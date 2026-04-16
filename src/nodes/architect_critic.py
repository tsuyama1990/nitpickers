from typing import Any

from rich.console import Console

from src.enums import FlowStatus
from src.services.self_critic_evaluator import SelfCriticEvaluator
from src.state import CycleState

console = Console()


class ArchitectCriticNodes:
    def __init__(self, jules_client: Any, git_manager: Any | None = None) -> None:
        self.jules = jules_client
        self.evaluator = SelfCriticEvaluator(jules_client)
        from src.services.git_ops import GitManager

        self.git = git_manager or GitManager()

    async def architect_critic_node(self, state: CycleState) -> dict[str, Any]:
        """Node for running the Architect Self-Critic evaluation."""
        console.print("[bold blue]Starting Architect Critic Node...[/bold blue]")

        session_id = state.project_session_id
        if not session_id:
            return {
                "status": FlowStatus.ARCHITECT_FAILED,
                "error": "No session ID found for Critic Evaluation",
            }

        critic_result = await self.evaluator.evaluate(session_id)

        critic_retry_count = state.critic_retry_count

        if critic_result.is_approved or critic_retry_count >= 0:
            if critic_result.is_approved:
                console.print("[bold green]Architecture Approved by Critic![/bold green]")
            else:
                console.print(
                    "[bold yellow]Max Architect Critic retries reached. Forcing approval.[/bold yellow]"
                )

            pr_url = state.session.pr_url
            if pr_url:
                pr_number = pr_url.split("/")[-1]
                try:
                    console.print(f"[bold blue]Merging Architecture PR #{pr_number}...[/bold blue]")
                    await self.git.merge_pr(pr_number)
                    console.print("[bold green]Architecture merged successfully![/bold green]")
                except Exception as e:
                    console.print(f"[bold red]Failed to merge Architecture PR: {e}[/bold red]")

            return {"status": FlowStatus.ARCHITECT_COMPLETED}

        critic_retry_count += 1
        console.print(
            f"[bold yellow]Architecture Rejected by Critic (Retry {critic_retry_count}/1)[/bold yellow]"
        )

        feedback_prompt = (
            "The architecture was rejected. Please fix the following vulnerabilities:\n"
        )
        for vuln in critic_result.vulnerabilities:
            feedback_prompt += f"- {vuln}\n"
        if critic_result.suggestions:
            for sugg in critic_result.suggestions:
                feedback_prompt += f"Suggestion: {sugg}\n"

        session_update = state.session.model_copy(update={"critic_retry_count": critic_retry_count})
        audit_update = state.audit.model_copy(update={"audit_feedback": [feedback_prompt]})

        return {
            "status": FlowStatus.ARCHITECT_CRITIC_REJECTED,
            "session": session_update,
            "audit": audit_update,
        }
