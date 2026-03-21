from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.panel import Panel

from src.config import settings
from src.services.llm_reviewer import LLMReviewer
from src.services.mcp_client_manager import McpClientManager
from src.services.plan_auditor import PlanAuditor

if TYPE_CHECKING:
    pass

console = Console()


class AuditOrchestrator:
    """
    Orchestrates the interactive planning loop between Jules and PlanAuditor.
    """

    def __init__(
        self,
        mcp_client: McpClientManager | None = None,
        sandbox_runner: Any = None,
        plan_auditor: PlanAuditor | None = None,
        llm_reviewer: LLMReviewer | None = None,
    ) -> None:
        self.mcp_client = mcp_client or McpClientManager()
        self.sandbox = sandbox_runner
        self.auditor = plan_auditor or PlanAuditor()
        self.llm_reviewer = llm_reviewer or LLMReviewer()

    async def run_interactive_session(
        self, prompt: str, spec_files: dict[str, str], max_retries: int = 3
    ) -> dict[str, Any]:
        """
        Starts a session with plan approval requirement and manages the audit loop.
        """
        console.print(Panel("[bold cyan]Starting AI-on-AI Audit Session[/bold cyan]", expand=False))

        file_paths = list(spec_files.keys())

        # We will use MCP directly via llm_reviewer and mcp_client
        async with self.mcp_client as client:
            tools = await client.get_orchestration_tools(server_name="jules")
            model = settings.reviewer.smart_model

            orchestration_prompt = (
                "You are the Audit Orchestrator. Dispatch agents via Jules MCP to fulfill the following:\n"
                f"{prompt}\n\n"
                f"Context files: {file_paths}\n"
                "Use `create_session` and return the resulting diffs."
            )

            response = await self.llm_reviewer._ainvoke_with_tools(  # type: ignore
                prompt=orchestration_prompt, model=model, tools=tools
            )

        return {"status": "success", "response": response}

