from typing import Any

from rich.console import Console

from src.config import settings
from src.enums import FlowStatus
from src.state import CycleState

console = Console()


class CoderCriticNodes:
    def __init__(self, jules_client: Any) -> None:
        self.jules = jules_client

    async def coder_critic_node(self, state: CycleState) -> dict[str, Any]:
        """Node for Coder Critic Evaluation phase."""
        from src.services.self_critic_evaluator import SelfCriticEvaluator

        console.print(
            f"[bold magenta]Starting Coder Critic for cycle: {state.cycle_id}[/bold magenta]"
        )

        session_id = state.jules_session_name
        if not session_id:
            from src.state_manager import StateManager

            mgr = StateManager()
            cycle_manifest = mgr.get_cycle(state.cycle_id)
            if cycle_manifest and cycle_manifest.jules_session_id:
                session_id = cycle_manifest.jules_session_id

        if not session_id:
            console.print(
                "[yellow]Warning: No active Jules session found for Coder Critic. Skipping.[/yellow]"
            )
            return {"status": FlowStatus.COMPLETED}

        evaluator = SelfCriticEvaluator(self.jules)

        console.print("[bold magenta]Invoking Coder Self-Critic Evaluator...[/bold magenta]")
        settings.get_prompt_content("POST_AUDIT_REFACTOR_INSTRUCTION.md")

        try:
            critic_result = await evaluator.evaluate(
                session_id,
                template_name="POST_AUDIT_REFACTOR_INSTRUCTION.md",
                cycle_id=state.cycle_id,
            )

            if not critic_result.is_approved:
                console.print(
                    "[bold yellow]Coder Critic identified improvements. Routing back to Coder.[/bold yellow]"
                )
                for vuln in critic_result.vulnerabilities:
                    console.print(f"[red] - {vuln}[/red]")
                return {"status": FlowStatus.CODER_RETRY}

        except Exception as e:
            console.print(f"[bold red]Coder Critic Evaluation failed: {e}[/bold red]")
            return {"status": FlowStatus.COMPLETED}

        else:
            console.print("[bold green]Coder Critic approved implementation.[/bold green]")
            return {"status": FlowStatus.COMPLETED}
