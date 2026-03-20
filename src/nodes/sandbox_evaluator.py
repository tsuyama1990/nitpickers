from typing import Any

from rich.console import Console

from src.config import settings
from src.domain_models.config import McpServerConfig
from src.domain_models.verification_schema import StructuralGateReport, VerificationResult
from src.enums import FlowStatus
from src.process_runner import ProcessRunner
from src.services.mcp_client_manager import McpClientManager
from src.state import CycleState

console = Console()


class SandboxEvaluatorNodes:
    """
    Evaluates the code and tests using the E2B Sandbox for Agentic TDD loop.
    """

    def __init__(
        self,
        mcp_manager: McpClientManager | None = None,
        process_runner: ProcessRunner | None = None,
    ) -> None:
        if mcp_manager is None:
            config = McpServerConfig(e2b_api_key=settings.E2B_API_KEY)
            self.mcp_manager = McpClientManager(config)
        else:
            self.mcp_manager = mcp_manager
        self.process_runner = process_runner or ProcessRunner()

        # Internal LLM for tool binding
        from langchain_openai import ChatOpenAI
        self.llm = ChatOpenAI(model=settings.reviewer.fast_model)

    async def sandbox_evaluate_node(self, state: CycleState) -> dict[str, Any]:
        """
        Executes the mechanical verification blockade: Linting, Type Checking, and Testing.
        All checks must pass with exit code 0 to proceed to the audit phase.
        """
        console.print("[bold cyan]Running Mechanical Verification Blockade...[/bold cyan]")

        try:
            timeout_limit = settings.sandbox.timeout

            import shlex

            # Retrieve tools and bind them here (even if currently unused in the legacy path, it initializes them)
            async with self.mcp_manager as mcp_client:
                tools = await mcp_client.get_tools()

                # Bind tools to the LLM
                _llm_with_tools = self.llm.bind_tools(tools)
                # In fully integrated system we would invoke the bound LLM here instead of ProcessRunner.
                # For Phase 1 we verify the LangChain tool bindings work, but we run via ProcessRunner.

            # Fallback to defaults if empty
            lint_cmd = settings.sandbox.lint_check_cmd or ["uv", "run", "ruff", "check", "."]
            type_cmd = settings.sandbox.type_check_cmd or ["uv", "run", "mypy", "."]

            # `test_cmd` might be a string based on `SandboxConfig`
            raw_test_cmd = settings.sandbox.test_cmd or "uv run pytest"
            if isinstance(raw_test_cmd, str):
                try:
                    test_cmd = shlex.split(raw_test_cmd)
                except ValueError:
                    test_cmd = raw_test_cmd.split()
            else:
                test_cmd = raw_test_cmd

            commands = {
                "lint": lint_cmd,
                "type": type_cmd,
                "test": test_cmd,
            }
            results = {}

            for check_name, cmd in commands.items():
                out, err, code, timeout_occurred = await self.process_runner.run_command(
                    cmd, check=False, timeout=timeout_limit
                )
                results[check_name] = VerificationResult(
                    command=" ".join(cmd),
                    exit_code=code,
                    stdout=out,
                    stderr=err,
                    timeout_occurred=timeout_occurred,
                )

            report = StructuralGateReport(
                lint_result=results["lint"],
                type_check_result=results["type"],
                test_result=results["test"],
            )

            if not report.passed:
                console.print(
                    "[bold red]Mechanical Blockade Enforced: Structural failure detected.[/bold red]"
                )
                error_trace = report.get_failure_report()

                return {
                    "status": FlowStatus.TDD_FAILED,
                    "error": f"Verification failed:\n{error_trace}",
                    "structural_report": report,
                }

        except Exception as e:
            console.print(f"[bold red]Execution Error in Verification Gate: {e}[/bold red]")
            return {
                "status": FlowStatus.TDD_FAILED,
                "error": f"Sandbox error: {e!s}",
            }
        else:
            console.print("[bold green]All structural checks passed. Ready for Audit.[/bold green]")
            return {
                "status": FlowStatus.READY_FOR_AUDIT,
                "structural_report": report,
                "error": None,
            }
