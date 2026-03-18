import asyncio
from datetime import UTC, datetime
from typing import Any

from rich.console import Console

from src.config import settings
from src.services.project import ProjectManager
from src.state import CycleState

console = Console()


class ArchitectNodes:
    def __init__(self, jules: Any, git: Any) -> None:
        self.jules = jules
        self.git = git

    async def architect_session_node(self, state: CycleState) -> dict[str, Any]:
        """Node for Architect Agent (Jules)."""
        console.print("[bold blue]Starting Architect Session...[/bold blue]")

        instruction = settings.get_template("ARCHITECT_INSTRUCTION.md").read_text()

        n = state.get("requested_cycle_count") or state.get("planned_cycle_count")

        if n:
            instruction = instruction.replace("{{max_cycles}}", str(n))
            instruction += (
                f"\n\nIMPORTANT CONSTRAINT: The development plan MUST be divided into "
                f"exactly {n} implementation cycles."
            )
        else:
            instruction = instruction.replace("{{max_cycles}}", "appropriate number of")

        timestamp = datetime.now(UTC).strftime("%Y%md%H%M%S")
        integration_branch = f"feat/generate-architecture-{timestamp}"

        try:
            await self.git.checkout_branch(integration_branch, create_if_not_exists=True)
            console.print(f"[dim]Working on integration branch: {integration_branch}[/dim]")
        except Exception as e:
            console.print(f"[bold red]Failed to setup architect branch: {e}[/bold red]")
            return {"status": "architect_failed", "error": f"Git checkout failed: {e}"}

        context_files = ["dev_documents/ALL_SPEC.md", "README.md", "README_DEVELOPER.md"]
        from anyio import Path

        if await Path("dev_documents/USER_TEST_SCENARIO.md").exists():
            context_files.append("dev_documents/USER_TEST_SCENARIO.md")

        result = await self.jules.execute_command(
            command="Design the system architecture based on ALL_SPEC.md.",
            session_id=f"architect-{timestamp}",
            prompt=instruction,
            target_files=context_files,
            context_files=[],
            require_plan_approval=False,
        )

        if (
            result.get("status") in ("success", "running")
            and result.get("pr_url")
            and result.get("session_name")
        ):
            session_name = result["session_name"]

            console.print(
                "[bold cyan]Initial Architecture PR created. "
                "Invoking Critic Agent for self-reflection...[/bold cyan]"
            )
            try:
                critic_instruction = settings.get_template(
                    "ARCHITECT_CRITIC_INSTRUCTION.md"
                ).read_text()
                session_url = self.jules._get_session_url(session_name)
                await self.jules._send_message(session_url, critic_instruction)

                console.print(
                    "[dim]Waiting for Critic Agent to finish review and push fixes...[/dim]"
                )
                await asyncio.sleep(10)

                result = await self.jules.wait_for_completion(session_name)
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Critic phase error, proceeding with initial PR: {e}[/yellow]"
                )

            if not result.get("pr_url"):
                return {
                    "status": "architect_failed",
                    "error": "Jules failed during the Critic phase or the PR was lost.",
                }

            pr_url = result["pr_url"]
            pr_number = pr_url.split("/")[-1]

            try:
                console.print(
                    f"[bold blue]Auto-merging Architecture PR #{pr_number}...[/bold blue]"
                )
                await self.git.merge_pr(pr_number)
                console.print("[bold green]Architecture merged successfully![/bold green]")

                try:
                    await ProjectManager().prepare_environment()
                except Exception as e:
                    console.print(f"[yellow]Warning: Environment preparation issue: {e}[/yellow]")

            except Exception as e:
                console.print(f"[bold red]Failed to auto-merge Architecture PR: {e}[/bold red]")

            return {
                "status": "architect_completed",
                "current_phase": "architect_done",
                "integration_branch": integration_branch,
                "active_branch": integration_branch,
                "project_session_id": session_name,
                "pr_url": pr_url,
            }

        if result.get("error"):
            return {"status": "architect_failed", "error": result.get("error")}

        return {"status": "architect_failed", "error": "Unknown Jules error or no PR URL"}

    async def _send_audit_feedback_to_session(
        self, session_id: str, feedback: str
    ) -> dict[str, Any] | None:
        console.print(
            f"[bold yellow]Sending Audit Feedback to existing Jules session: {session_id}[/bold yellow]"
        )
        try:
            feedback_template = str(settings.get_template("AUDIT_FEEDBACK_MESSAGE.md").read_text())
            feedback_msg = feedback_template.replace("{{feedback}}", feedback)
            await self.jules._send_message(self.jules._get_session_url(session_id), feedback_msg)
            console.print(
                "[dim]Waiting for Jules to process feedback (expecting IN_PROGRESS)...[/dim]"
            )

            state_transitioned = False
            for attempt in range(12):
                await asyncio.sleep(5)
                current_state = await self.jules.get_session_state(session_id)
                console.print(f"[dim]State check ({attempt + 1}/12): {current_state}[/dim]")

                if current_state in {
                    "IN_PROGRESS",
                    "QUEUED",
                    "PLANNING",
                    "AWAITING_PLAN_APPROVAL",
                    "AWAITING_USER_FEEDBACK",
                    "PAUSED",
                }:
                    state_transitioned = True
                    console.print(
                        "[green]Jules session is now active. Proceeding to monitor...[/green]"
                    )
                    break
                if current_state == "FAILED":
                    console.print("[red]Jules session failed during feedback wait.[/red]")
                    return None

            if not state_transitioned:
                console.print(
                    "[yellow]Warning: Jules session state did not change to IN_PROGRESS after 60s. "
                    "Assuming message received but state lagging, or task finished very quickly.[/yellow]"
                )

            result = await self.jules.wait_for_completion(session_id)

        except Exception as e:
            console.print(
                f"[yellow]Failed to send feedback to existing session: {e}. Creating new session...[/yellow]"
            )
            return None

        if result.get("status") == "success" or result.get("pr_url"):
            return {"status": "ready_for_audit", "pr_url": result.get("pr_url")}

        console.print(
            "[yellow]Jules session finished without new PR. Creating new session...[/yellow]"
        )
        return None
