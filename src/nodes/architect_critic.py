from typing import Any

from rich.console import Console

from src.services.self_critic_evaluator import SelfCriticEvaluator
from src.state import CycleState

console = Console()


class ArchitectCriticNodes:
    def __init__(self, mcp_client: Any = None) -> None:
        self.mcp_client = mcp_client
        self.evaluator = SelfCriticEvaluator(mcp_client)

    async def architect_critic_node(self, state: CycleState) -> dict[str, Any]:
        """Node for running the Architect Self-Critic evaluation."""
        console.print("[bold blue]Starting Architect Critic Node...[/bold blue]")

        session_id = state.project_session_id
        if not session_id:
            return {
                "status": "architect_failed",
                "error": "No session ID found for Critic Evaluation",
            }

        critic_result = await self.evaluator.evaluate(session_id)

        critic_retry_count = state.critic_retry_count

        if critic_result.is_approved:
            console.print("[bold green]Architecture Approved by Critic![/bold green]")
            return {"status": "architect_completed"}

        critic_retry_count += 1
        console.print(
            f"[bold yellow]Architecture Rejected by Critic (Retry {critic_retry_count}/3)[/bold yellow]"
        )

        for vuln in critic_result.vulnerabilities:
            console.print(f"[red] - {vuln}[/red]")

        if critic_retry_count >= 3:
            console.print(
                "[bold red]Max Architect Critic retries reached. Forcing approval or failing gracefully.[/bold red]"
            )
            return {
                "status": "architect_failed",
                "error": "Max Architect Critic retries reached with vulnerabilities.",
                "critic_retry_count": critic_retry_count,
            }

        feedback_prompt = (
            "The architecture was rejected. Please fix the following vulnerabilities:\n"
        )
        for vuln in critic_result.vulnerabilities:
            feedback_prompt += f"- {vuln}\n"
        if critic_result.suggestions:
            for sugg in critic_result.suggestions:
                feedback_prompt += f"Suggestion: {sugg}\n"

        return {
            "status": "architect_critic_rejected",
            "critic_retry_count": critic_retry_count,
            "audit_feedback": [feedback_prompt],
        }
