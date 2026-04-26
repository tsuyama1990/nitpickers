from typing import Any

from rich.console import Console

from src.enums import FlowStatus
from src.state import CycleState

console = Console()


class CoderCriticNodes:
    def __init__(self, jules_client: Any) -> None:
        self.jules = jules_client

    async def coder_critic_node(self, state: CycleState) -> dict[str, Any]:
        """Node for Coder Self-Critic phase."""
        from src.services.coder_usecase import CoderUseCase

        usecase = CoderUseCase(self.jules)
        cycle_id = state.cycle_id
        session_id = state.session.jules_session_name

        if not session_id:
            return {"status": FlowStatus.FAILED, "error": "No session ID for critic phase"}

        is_final = (
            state.status == FlowStatus.READY_FOR_FINAL_CRITIC
            or getattr(state.committee, "is_refactoring", False)
            or getattr(state, "final_fix", False)
        )
        result = await usecase.run_critic_phase(state, cycle_id, session_id, is_final=is_final)

        if not result:
            return {"status": FlowStatus.FAILED, "error": "Critic phase failed to produce result"}

        # Preserve PR and branch info
        pr_url = result.get("pr_url") or state.session.pr_url
        branch_name = result.get("branch_name") or state.session.branch_name

        session_update = state.session.model_copy(
            update={"pr_url": pr_url, "branch_name": branch_name}
        )

        # If it's a final polish or post-audit refactor, we are COMPLETED.
        new_status = FlowStatus.COMPLETED if is_final else FlowStatus.READY_FOR_AUDIT

        # --- Explicit PR Checkpoint Notification ---
        if pr_url:
            phase_type = "Final Critic" if is_final else "Self-Critic"
            console.print(f"[bold green]PR Point [{phase_type}]:[/bold green] {pr_url}")

        return {
            "status": new_status,
            "session": session_update,
            "branch_name": branch_name,
            "pr_url": pr_url,
        }
