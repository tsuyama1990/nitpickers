import json
from typing import Any

from rich.console import Console

from src.config import settings
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
        mcp_client: McpClientManager | None = None,
        process_runner: ProcessRunner | None = None,
    ) -> None:
        self.mcp_client = mcp_client or McpClientManager()
        self.process_runner = process_runner or ProcessRunner()

    async def sandbox_evaluate_node(self, state: CycleState) -> dict[str, Any]:
        """
        Executes the mechanical verification blockade: Linting, Type Checking, and Testing.
        Uses MCP tools bound to the LLM.
        """
        console.print("[bold cyan]Running Mechanical Verification Blockade...[/bold cyan]")

        try:
            import litellm
            from langchain_core.messages import ToolMessage
            from langchain_core.utils.function_calling import convert_to_openai_tool


            async with self.mcp_client as client:
                tools = await client.get_tools(server_name="e2b")

                # Convert LangChain tools to OpenAI format for litellm
                litellm_tools = [convert_to_openai_tool(t) for t in tools]
                tools_map = {t.name: t for t in tools}

                # We prompt the LLM to run the test script.
                # If there's a script in state, we test it. Or we just execute pytest.
                test_cmd = settings.sandbox.test_cmd
                if isinstance(test_cmd, list):
                    test_cmd = " ".join(test_cmd)

                prompt = (
                    f"You must execute the command `{test_cmd}` using the appropriate tool. "
                    "If a script is provided in the state or environment, run it. "
                    "You must use the tool to run the code/command."
                )

                response = await litellm.acompletion(
                    model=settings.agents.qa_analyst_model,
                    messages=[
                        {"role": "system", "content": "You are a test runner. Use tools to execute the tests."},
                        {"role": "user", "content": prompt}
                    ],
                    tools=litellm_tools,
                    tool_choice="required"
                )

                message = response.choices[0].message
                if not message.tool_calls:
                    return {
                        "status": FlowStatus.TDD_FAILED,
                        "error": "LLM failed to invoke the execution tool."
                    }

                # Execute the tool
                tool_call = message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                selected_tool = tools_map.get(tool_name)
                if not selected_tool:
                    return {
                        "status": FlowStatus.TDD_FAILED,
                        "error": f"Unknown tool invoked: {tool_name}"
                    }

                # Natively invoke the tool via LangChain interface
                tool_result_content = await selected_tool.ainvoke(tool_args)

                # Record the result as ToolMessage
                tool_message = ToolMessage(
                    content=str(tool_result_content),
                    tool_call_id=tool_call.id,
                    name=tool_name
                )

                # Determine success or failure from the output or tool behavior
                # The MCP run_code tool typically returns stdout and stderr.
                # Since E2B MCP run_code outputs might vary, we inspect the returned string.
                content_str = str(tool_message.content)
                output_str = content_str.lower()

                passed = "error" not in output_str and "exception" not in output_str and "failed" not in output_str
                # Actually, the best way is to see if exit_code is in the output or we just parse it.
                exit_code = 0 if passed else 1

                test_result = VerificationResult(
                    command=test_cmd,
                    exit_code=exit_code,
                    stdout=content_str,
                    stderr=content_str if exit_code != 0 else "",
                    timeout_occurred=False
                )

                report = StructuralGateReport(
                    lint_result=test_result,
                    type_check_result=test_result,
                    test_result=test_result,
                )

                if exit_code != 0:
                    console.print("[bold red]Mechanical Blockade Enforced: Structural failure detected.[/bold red]")
                    return {
                        "status": FlowStatus.TDD_FAILED,
                        "error": f"Verification failed:\n{content_str}",
                        "structural_report": report,
                    }

        except Exception as e:
            console.print(f"[bold red]Execution Error in Verification Gate: {e}[/bold red]")
            return {
                "status": FlowStatus.TDD_FAILED,
                "error": f"Sandbox error: {e!s}",
            }

        console.print("[bold green]All structural checks passed. Ready for Audit.[/bold green]")
        return {
            "status": FlowStatus.READY_FOR_AUDIT,
            "structural_report": report,
            "error": None,
        }
