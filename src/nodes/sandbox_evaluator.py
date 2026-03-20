from typing import Any

from rich.console import Console

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
            # 1. Run Linting (Ruff)
            lint_cmd = ["uv", "run", "ruff", "check", "."]
            l_out, l_err, l_code = await self.process_runner.run_command(lint_cmd, check=False)
            lint_result = VerificationResult(
                command=" ".join(lint_cmd), exit_code=l_code, stdout=l_out, stderr=l_err
            )

            # 2. Run Type Checking (Mypy)
            type_cmd = ["uv", "run", "mypy", "."]
            t_out, t_err, t_code = await self.process_runner.run_command(type_cmd, check=False)
            type_result = VerificationResult(
                command=" ".join(type_cmd), exit_code=t_code, stdout=t_out, stderr=t_err
            )

            # 3. Run Testing (Pytest)
            test_cmd = ["uv", "run", "pytest"]
            p_out, p_err, p_code = await self.process_runner.run_command(test_cmd, check=False)
            test_result = VerificationResult(
                command=" ".join(test_cmd), exit_code=p_code, stdout=p_out, stderr=p_err
            )

            report = StructuralGateReport(
                lint_result=lint_result,
                type_check_result=type_result,
                test_result=test_result,
            )

            if not report.passed:
                console.print("[bold red]Mechanical Blockade Enforced: Structural failure detected.[/bold red]")
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
