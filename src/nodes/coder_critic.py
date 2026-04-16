from typing import Any

from rich.console import Console

from src.enums import FlowStatus
from src.state import CycleState

console = Console()


class CoderCriticNodes:
    def __init__(self, jules_client: Any) -> None:
        self.jules = jules_client

    async def coder_critic_node(self, state: CycleState) -> dict[str, Any]:
        """Node deprecated as CoderUseCase handles self-critic internally.
        Passing through to avoid breaking the graph structure."""
        return {"status": FlowStatus.COMPLETED}
