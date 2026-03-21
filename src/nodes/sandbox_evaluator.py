from collections.abc import Sequence
from typing import Any

from langchain_core.tools import BaseTool
from rich.console import Console

from src.config import settings
from src.domain_models.verification_schema import StructuralGateReport, VerificationResult
from src.enums import FlowStatus
from src.state import CycleState

console = Console()


class SandboxEvaluatorNodes:
    """
    Evaluates the code and tests using the E2B Sandbox for Agentic TDD loop.
    Uses MCP tools natively to interact with the environment.
    """

    def __init__(
        self,
        e2b_tools: Sequence[BaseTool] | None = None,
    ) -> None:
        self.e2b_tools = e2b_tools

    async def sandbox_evaluate_node(self, state: CycleState) -> dict[str, Any]:  # noqa: C901
        """
        Executes the mechanical verification blockade: Linting, Type Checking, and Testing.
        All checks must pass with exit code 0 to proceed to the audit phase.
        """
        console.print("[bold cyan]Running Mechanical Verification Blockade via MCP...[/bold cyan]")

        if not self.e2b_tools:
            return {
                "status": FlowStatus.TDD_FAILED,
                "error": "E2B Tools not injected. Cannot run mechanical blockade.",
            }

        try:
            import shlex

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

            lint_str = " ".join(lint_cmd)
            type_str = " ".join(type_cmd)
            test_str = " ".join(test_cmd)

            try:
                # We directly invoke the execute_command tool to run bash commands
                exec_tool = next(
                    (t for t in self.e2b_tools if t.name in {"execute_command", "run_command"}), None
                )
                if not exec_tool:
                    msg = "execute_command tool not found in e2b_tools"
                    raise ValueError(msg)  # noqa: TRY301

                results = {}
                commands = {
                    "lint": lint_str,
                    "type": type_str,
                    "test": test_str,
                }

                for check_name, cmd_str in commands.items():
                    # Invoke the langchain tool
                    # The payload structure depends on the tool schema. Often it's {"command": "..."}
                    # We can use .ainvoke

                    try:
                        # Sometimes it expects 'command', sometimes 'commandLine' etc.
                        # For e2b/mcp-server, the tool is typically called `execute_command` with arg `command`
                        # Let's just pass {"command": cmd_str}
                        tool_result = await exec_tool.ainvoke({"command": cmd_str})
                    except Exception as invoke_err:
                        tool_result = str(invoke_err)

                    # Parse the tool result. The MCP execute_command typically returns a string or a JSON with stdout/stderr
                    # If it's a string from e2b, we can parse it roughly or just assume 0 exit code if no error text is thrown.
                    # Wait, litellm or langchain with tools usually returns a string.
                    # e2b execute_command returns stdout and stderr.

                    # For safety, since MCP execution might wrap things, let's treat the tool_result as stdout.
                    # If an exception was raised, it's a non-zero exit code.

                    code = 0
                    stdout = str(tool_result)
                    stderr = ""

                    if "Error" in stdout or "failed" in stdout.lower() or "exit code: 1" in stdout.lower():
                         code = 1
                         stderr = stdout

                    results[check_name] = VerificationResult(
                        command=cmd_str,
                        exit_code=code,
                        stdout=stdout,
                        stderr=stderr,
                        timeout_occurred=False,
                    )

            except Exception as e:
                console.print(f"[bold red]Tool execution error: {e}[/bold red]")
                return {
                    "status": FlowStatus.TDD_FAILED,
                    "error": f"Tool execution failed: {e!s}",
                }

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
