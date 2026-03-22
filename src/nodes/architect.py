import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from langchain_core.tools import BaseTool
from rich.console import Console

from src.config import settings
from src.services.project import ProjectManager
from src.state import CycleState

console = Console()


class ArchitectNodes:
    def __init__(self, github_read_tools: Sequence[BaseTool] | None = None) -> None:


        self.github_read_tools = github_read_tools

    async def architect_session_node(self, state: CycleState) -> dict[str, Any]:  # noqa: C901
        """Node for Architect Agent (Jules)."""
        console.print("[bold blue]Starting Architect Session...[/bold blue]")

        # Handle feedback loop from architect_critic_node
        session_id = state.get("project_session_id")
        if state.get("status") == "architect_critic_rejected" and session_id:
            feedback = ""
            if state.get("audit_feedback"):
                feedback = "\n".join(state.audit_feedback)
            result = await self.send_audit_feedback_to_session(str(session_id), feedback)
            if result and result.get("pr_url"):
                pr_url = result["pr_url"]
                pr_number = pr_url.split("/")[-1]
                try:
                    console.print(
                        f"[bold blue]Auto-merging updated Architecture PR #{pr_number}...[/bold blue]"
                    )
                    console.print(
                        "[bold green]Architecture updated and merged successfully![/bold green]"
                    )
                except Exception as e:
                    console.print(f"[bold red]Failed to auto-merge Architecture PR: {e}[/bold red]")

                return {
                    "status": "architect_completed",
                    "current_phase": "architect_done",
                    "pr_url": pr_url,
                }
            return {
                "status": "architect_failed",
                "error": "Failed to handle architect critic feedback.",
            }

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
            console.print(f"[dim]Working on integration branch: {integration_branch}[/dim]")
        except Exception as e:
            console.print(f"[bold red]Failed to setup architect branch: {e}[/bold red]")
            return {"status": "architect_failed", "error": f"Git checkout failed: {e}"}

        context_files = ["dev_documents/ALL_SPEC.md", "README.md", "README_DEVELOPER.md"]
        from anyio import Path

        if await Path("dev_documents/USER_TEST_SCENARIO.md").exists():
            context_files.append("dev_documents/USER_TEST_SCENARIO.md")

        new_result: dict[str, Any] = {}

        if (
            new_result.get("status") in ("success", "running")
            and new_result.get("pr_url")
            and new_result.get("session_name")
        ):
            session_name = new_result["session_name"]

            pr_url = new_result["pr_url"]
            pr_number = pr_url.split("/")[-1]

            try:
                console.print(
                    f"[bold blue]Auto-merging Architecture PR #{pr_number}...[/bold blue]"
                )
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

        if new_result.get("error"):
            return {"status": "architect_failed", "error": new_result.get("error")}

        return {"status": "architect_failed", "error": "Unknown Jules error or no PR URL"}

    async def send_audit_feedback_to_session(
        self, session_id: str, feedback: str
    ) -> dict[str, Any] | None:
        console.print(
            f"[bold yellow]Sending Audit Feedback to existing Jules session: {session_id}[/bold yellow]"
        )
        try:
            console.print(
                "[dim]Waiting for Jules to process feedback (expecting IN_PROGRESS)...[/dim]"
            )

            state_transitioned = False
            for attempt in range(12):
                await asyncio.sleep(5)
                current_state = "IN_PROGRESS"
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

            result: dict[str, Any] = {}

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
