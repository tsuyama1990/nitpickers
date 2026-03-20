from typing import Any

from rich.console import Console

from src.config import settings
from src.contracts.e2b_executor import E2BExecutorService
from src.domain_models.verification_schema import StructuralGateReport, VerificationResult
from src.enums import FlowStatus
from src.process_runner import ProcessRunner
from src.services.e2b_executor import E2BExecutorServiceImpl
from src.state import CycleState

console = Console()


class SandboxEvaluatorNodes:
    """
    Evaluates the code and tests using the E2B Sandbox for Agentic TDD loop.
    """

    def __init__(
        self,
        executor: E2BExecutorService | None = None,
        process_runner: ProcessRunner | None = None,
    ) -> None:
        self.executor = executor or E2BExecutorServiceImpl()
        self.process_runner = process_runner or ProcessRunner()

    async def sandbox_evaluate_node(self, state: CycleState) -> dict[str, Any]:
        """
        Executes the mechanical verification blockade: Linting, Type Checking, and Testing.
        All checks must pass with exit code 0 to proceed to the audit phase.
        """
        console.print("[bold cyan]Running Mechanical Verification Blockade...[/bold cyan]")

        try:
            timeout_limit = settings.sandbox.timeout

            commands = {
                "lint": ["uv", "run", "ruff", "check", "."],
                "type": ["uv", "run", "mypy", "."],
                "test": ["uv", "run", "pytest"],
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
