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

    _FORBIDDEN_CHARS = None

    def __init__(
        self,
        e2b_tools: Sequence[BaseTool] | None = None,
    ) -> None:
        self.e2b_tools = e2b_tools

    @classmethod
    def _get_forbidden_chars_pattern(cls) -> Any:
        if cls._FORBIDDEN_CHARS is None:
            import re
            cls._FORBIDDEN_CHARS = re.compile(r"[&|<>;$`\\]")
        return cls._FORBIDDEN_CHARS

    def _get_execution_tool(self) -> tuple[BaseTool, str] | None:
        """Finds the tool capable of executing shell commands and its primary argument."""
        if not self.e2b_tools:
            return None

        exec_tool = next(
            (t for t in self.e2b_tools if t.name in {"execute_command", "run_command"}), None
        )

        if not exec_tool:
            for tool in self.e2b_tools:
                if getattr(tool, "args_schema", None):
                    schema = tool.args_schema.schema()
                    props = schema.get("properties", {})
                    if "command" in props or "commandLine" in props:
                        exec_tool = tool
                        break

        if not exec_tool:
            return None

        arg_name = "command"
        if getattr(exec_tool, "args_schema", None):
            props = exec_tool.args_schema.schema().get("properties", {})
            if props:
                arg_name = next(iter(props.keys()))

        return exec_tool, arg_name

    async def sandbox_evaluate_node(self, state: CycleState) -> dict[str, Any]:  # noqa: C901, PLR0912, PLR0915
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
                tool_info = self._get_execution_tool()
                if not tool_info:
                    msg = "Tool with a command schema could not be discovered among e2b_tools."
                    raise ValueError(msg)  # noqa: TRY301

                exec_tool, arg_name = tool_info

                results = {}
                commands = {
                    "lint": lint_str,
                    "type": type_str,
                    "test": test_str,
                }

                forbidden_chars = self._get_forbidden_chars_pattern()

                for check_name, cmd_str in commands.items():
                    if not cmd_str or not cmd_str.strip():
                        msg = f"Command for {check_name} is empty."
                        raise ValueError(msg)  # noqa: TRY301

                    if forbidden_chars.search(cmd_str):
                        msg = f"Dangerous characters detected in {check_name} command."
                        raise ValueError(msg)  # noqa: TRY301

                    timeout_occurred = False
                    code = 0
                    stdout = ""
                    stderr = ""

                    try:
                        import asyncio
                        # Using wait_for to prevent infinite hanging
                        tool_result = await asyncio.wait_for(
                            exec_tool.ainvoke({arg_name: cmd_str}),
                            timeout=settings.sandbox.timeout
                        )
                        stdout = str(tool_result)
                        if "Error" in stdout or "failed" in stdout.lower() or "exit code: 1" in stdout.lower():
                            code = 1
                            stderr = stdout
                    except TimeoutError:
                        stderr = f"Error: Command timed out after {settings.sandbox.timeout} seconds"
                        timeout_occurred = True
                        code = 124  # Standard bash exit code for timeout
                    except ConnectionError as conn_err:
                        stderr = f"Connection Error to MCP Server: {conn_err}"
                        code = 1
                    except Exception as invoke_err:
                        import logging

                        logger = logging.getLogger(__name__)
                        logger.exception("Unexpected error executing tool")
                        stderr = f"Execution Error: {invoke_err}"
                        code = 1

                    results[check_name] = VerificationResult(
                        command=cmd_str,
                        exit_code=code,
                        stdout=stdout,
                        stderr=stderr,
                        timeout_occurred=timeout_occurred,
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
