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
        from src.services.mcp_client_manager import McpClientManager
        self.jules = jules
        self.git = git
        self.mcp_client = McpClientManager()

    async def architect_session_node(self, state: CycleState) -> dict[str, Any]:  # noqa: C901, PLR0912, PLR0915
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
                    await self.git.merge_pr(pr_number)
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
            await self.git.create_feature_branch(integration_branch)
            console.print(f"[dim]Working on integration branch: {integration_branch}[/dim]")
        except Exception as e:
            console.print(f"[bold red]Failed to setup architect branch: {e}[/bold red]")
            return {"status": "architect_failed", "error": f"Git checkout failed: {e}"}

        context_files = ["dev_documents/ALL_SPEC.md", "README.md", "README_DEVELOPER.md"]
        from anyio import Path

        if await Path("dev_documents/USER_TEST_SCENARIO.md").exists():
            context_files.append("dev_documents/USER_TEST_SCENARIO.md")

        # Autonomous file gathering via LLM and MCP Tools
        gathered_context = ""
        try:
            async with self.mcp_client as client:
                tools = await client.get_readonly_tools("github")

                # We must provide the repo context dynamically so the tools actually work.
                repo_context = ""
                try:
                    owner, repo_name, _ = await self.jules.git_context.prepare_git_context()
                    repo_context = f"\nRepository: {owner}/{repo_name}"
                except Exception:
                    repo_context = "\nRepository: local"

                messages: list[dict[str, Any]] = [
                    {
                        "role": "system",
                        "content": f"You are gathering extra context to design the system architecture.{repo_context}\n"
                                   "Use the provided tools to explore the repository if needed (e.g., checking package.json, directory structure). "
                                   "Once you have gathered enough context, just reply with 'DONE'. DO NOT design the architecture yet."
                    },
                    {
                        "role": "user",
                        "content": "Please explore the repository to gather any additional useful context beyond the main specifications."
                    }
                ]

                from src.services.react_agent import execute_react_loop

                extra_args = {}
                if "owner" in locals() and "repo_name" in locals():
                    extra_args["repo"] = f"{owner}/{repo_name}"

                await execute_react_loop(
                    model=settings.agents.qa_analyst_model,
                    messages=messages,
                    tools=tools,
                    max_loops=5,
                    temperature=0.0,
                    extra_tool_args=extra_args
                )

                # Reconstruct gathered context from the message history generated by ReAct
                for msg in messages:
                    if msg.get("role") == "tool":
                        t_name = msg.get("name")
                        t_content = msg.get("content")
                        gathered_context += f"\n\n--- File Content (via {t_name}) ---\n{t_content}"

        except Exception as e:
            console.print(f"[bold yellow]Warning: Failed to gather context via LLM: {e}[/bold yellow]")

        final_instruction = instruction
        if gathered_context:
            final_instruction += f"\n\n=== REPOSITORY CONTEXT ===\n{gathered_context}"

        exec_func = getattr(self.jules, "execute_command", getattr(self.jules, "run_session", None))
        result = await exec_func(  # type: ignore[misc]
            command="Design the system architecture based on ALL_SPEC.md.",
            session_id=f"architect-{timestamp}",
            prompt=final_instruction,
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

    async def send_audit_feedback_to_session(
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
