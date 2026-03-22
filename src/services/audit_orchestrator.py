from collections.abc import Sequence
from typing import Any

from langchain_core.tools import BaseTool
from rich.console import Console
from rich.panel import Panel

from src.services.plan_auditor import PlanAuditor

console = Console()


class AuditOrchestrator:
    """
    Orchestrates the interactive planning loop between Jules and PlanAuditor.
    """

    def __init__(
        self,
        jules_tools: Sequence[BaseTool] | None = None,
        sandbox_runner: Any | None = None,
        plan_auditor: PlanAuditor | None = None,
    ) -> None:
        self.jules_tools = jules_tools or []
        self.sandbox = sandbox_runner
        self.auditor = plan_auditor or PlanAuditor()

    async def run_interactive_session(
        self, prompt: str, spec_files: dict[str, str], max_retries: int = 3
    ) -> dict[str, Any]:
        """
        Starts a session with plan approval requirement and manages the audit loop.
        """
        console.print(Panel("[bold cyan]Starting AI-on-AI Audit Session[/bold cyan]", expand=False))

        file_paths = list(spec_files.keys())

        # Placeholder logic:
        # In actual MCP architecture, jules_tools manages this session interaction
        # We replace the old jules HTTP wrapper loops with an MCP-based orchestrator flow.
        from litellm import acompletion

        messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
        tools_schema = [{"type": "function", "function": {"name": t.name, "description": t.description}} for t in self.jules_tools] if self.jules_tools else None

        retry_count = 0
        while retry_count <= max_retries:
            response = await acompletion(
                model="gpt-4o",
                messages=messages,
                tools=tools_schema
            )

            content = response.choices[0].message.content or "No plan provided."
            plan_details = {"plan": content, "planId": f"plan_{retry_count}"}

            console.print(
                Panel(
                    content,
                    title="[bold cyan]Proposed Plan[/bold cyan]",
                    expand=False,
                )
            )

            audit_result = await self.auditor.audit_plan(
                plan_details, spec_files, phase="architect"
            )

            if audit_result.status == "APPROVED":
                console.print("[bold green]Plan Approved![/bold green]")
                return {"status": "SUCCESS"}

            retry_count += 1
            if retry_count > max_retries:
                console.print("[bold red]Max retries exceeded. Aborting session.[/bold red]")
                return {"status": "FAILED_AUDIT_LIMIT", "feedback": audit_result.reason}

            feedback_prompt = (
                f"The plan was REJECTED by the Auditor.\n\nReason:\n{audit_result.reason}\n\n"
                "Please generate a revised plan based on this feedback."
            )

            console.print(f"[magenta]Sending Feedback to Agent:[/magenta] {audit_result.reason}")
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": feedback_prompt})

        u_msg = "Session ended unexpectedly."
        raise RuntimeError(u_msg)
