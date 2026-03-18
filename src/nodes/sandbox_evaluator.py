from typing import Any

from rich.console import Console

from src.config import settings
from src.contracts.e2b_executor import E2BExecutorService
from src.enums import FlowStatus
from src.services.e2b_executor import E2BExecutorServiceImpl
from src.state import CycleState

console = Console()


class SandboxEvaluatorNodes:
    """
    Evaluates the code and tests using the E2B Sandbox for Agentic TDD loop.
    """

    def __init__(self, executor: E2BExecutorService | None = None) -> None:
        self.executor = executor or E2BExecutorServiceImpl()

    async def sandbox_evaluate_node(self, state: CycleState) -> dict[str, Any]:
        """
        Executes the Red-Green-Refactor logic inside an E2B Sandbox.
        """
        console.print("[bold cyan]Running Agentic TDD Evaluation in Sandbox...[/bold cyan]")

        # Get phase, default to green if not set to assume standard run
        tdd_phase = state.tdd_phase or "green"

        try:
            # Sync files and run pytest
            pytest_cmd = getattr(settings.sandbox, "test_cmd", "uv run pytest -v --tb=short")
            result = await self.executor.run_tests(str(pytest_cmd))

            console.print(f"[dim]Sandbox Execution Exit Code: {result.exit_code}[/dim]")
            # Note: We omit dumping the raw stdout/stderr to the console directly
            # to prevent potential information disclosure. They are stored in
            # `sandbox_artifacts` for processing by subsequent AI nodes.

            # Evaluate based on Red-Green phase
            is_success = result.exit_code == 0

            if tdd_phase == "red":
                if is_success:
                    # Test passed immediately without implementation -> bad
                    msg = "Test passed immediately; it must fail first to prove valid assertions."
                    console.print(f"[bold red]TDD Failure: {msg}[/bold red]")
                    return {
                        "status": FlowStatus.UAT_FAILED,
                        "error": msg,
                        "sandbox_artifacts": result.model_dump(),
                        "tdd_phase": "red",
                    }

                # Test failed -> good (valid failing test)
                console.print(
                    "[bold green]Failing test confirmed (Red Phase complete). Requesting implementation...[/bold green]"
                )
                return {
                    "status": FlowStatus.READY_FOR_AUDIT,
                    "sandbox_artifacts": result.model_dump(),
                    "tdd_phase": "green",  # transition to green phase for next run
                }

            # Green Phase evaluation
            if is_success:
                # Tests passed -> good (implementation works)
                console.print(
                    "[bold green]Tests passed (Green Phase complete). Ready for Audit.[/bold green]"
                )
                return {
                    "status": FlowStatus.READY_FOR_AUDIT,
                    "sandbox_artifacts": result.model_dump(),
                    "tdd_phase": "green",
                }

            # Tests failed -> bad (implementation is broken)
            error_msg = f"Execution failed. Fix this: \n{result.stderr}\n{result.stdout}"
            console.print(
                "[bold red]Tests failed in Green Phase. Routing back to Coder...[/bold red]"
            )
            return {
                "status": FlowStatus.UAT_FAILED,
                "error": error_msg,
                "sandbox_artifacts": result.model_dump(),
                "tdd_phase": "green",  # stay in green phase until fixed
            }

        except Exception as e:
            console.print(f"[bold red]Sandbox Execution Error: {e}[/bold red]")
            return {
                "status": FlowStatus.UAT_FAILED,
                "error": f"Sandbox error: {e!s}",
                "tdd_phase": tdd_phase,
            }
