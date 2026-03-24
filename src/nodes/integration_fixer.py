import uuid
from typing import Any

from rich.console import Console

from src.config import settings
from src.state import IntegrationState

console = Console()


class IntegrationFixerNodes:
    def __init__(self, jules_client: Any) -> None:
        self.jules_client = jules_client

    async def integration_fixer_node(self, state: IntegrationState) -> dict[str, Any]:
        """Resolves logical errors across the integrated codebase after a successful merge."""
        console.print(
            "[bold cyan]Invoking Integration Fixer to resolve logical regressions...[/bold cyan]"
        )

        # We need a session name to communicate with Jules
        session_id = state.master_integrator_session_id
        if not session_id:
            session_id = f"integration-fixer-{uuid.uuid4().hex[:6]}"

        prompt = (
            "You are the Integration Fixer. A recent git merge was successful, but the global "
            "unit tests or linters are failing. Please run the validation suite (e.g., `uv run pytest`, "
            "`uv run ruff check .`, `uv run mypy .`), diagnose the logical regressions, and fix them.\n\n"
            "Do not introduce new features. Your only goal is to make the CI/CD pipeline green again."
        )

        try:
            # We will use run_session to let the agent fix the codebase.
            await self.jules_client.run_session(
                session_id=session_id,
                prompt=prompt,
                target_files=settings.get_target_files(),
                context_files=settings.get_context_files(),
                require_plan_approval=False,
            )
        except Exception as e:
            console.print(f"[bold red]Integration Fixer Error: {e}[/bold red]")
            return {"master_integrator_session_id": session_id}
        else:
            return {"master_integrator_session_id": session_id}
