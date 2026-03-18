from typing import Any

from rich.console import Console

from src.enums import FlowStatus
from src.services.coder_usecase import CoderUseCase
from src.state import CycleState

console = Console()


class CoderCriticNodes:
    def __init__(self, jules: Any) -> None:
        self.jules = jules

    async def coder_critic_node(self, state: CycleState) -> dict[str, Any]:
        """Runs the coder critic phase."""
        console.print("[bold magenta]Running Coder Critic Phase...[/bold magenta]")
        state.status = FlowStatus.POST_AUDIT_REFACTOR

        usecase = CoderUseCase(self.jules)
        result = await usecase.execute(state)

        # The coder usecase execute handles sending the post audit refactor instruction
        # and checking the result.

        return dict(result)

def route_coder_critic(state: CycleState) -> str:
    """Routes after the Coder Critic Node."""
    if state.status == FlowStatus.COMPLETED:
        return "uat_evaluate"
    return "coder_session"
