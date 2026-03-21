import asyncio
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

from src.config import settings
from src.domain_models import AuditResult
from src.enums import FlowStatus
from src.services.git_ops import GitManager
from src.services.jules_client import JulesClient
from src.services.llm_reviewer import LLMReviewer
from src.state import CycleState
from src.state_manager import StateManager

console = Console()


class QaUseCase:
    """
    Encapsulates the QA Session and Auditor logic.
    """

    def __init__(
        self, jules_client: JulesClient, git_manager: GitManager, llm_reviewer: LLMReviewer, mcp_client: Any = None
    ) -> None:
        if not jules_client or not git_manager or not llm_reviewer:
            msg = "Missing required dependencies injected into QaUseCase"
            raise ValueError(msg)
        self.jules = jules_client
        self.git = git_manager
        self.llm_reviewer = llm_reviewer
        from src.services.mcp_client_manager import McpClientManager
        self.mcp_client = mcp_client or McpClientManager()

    async def _send_audit_feedback_to_session(
        self, session_id: str, feedback: str
    ) -> dict[str, Any] | None:
        console.print(
            f"[bold yellow]Sending Audit Feedback to existing Jules session: {session_id}[/bold yellow]"
        )
        try:
            await self.jules._send_message(self.jules._get_session_url(session_id), feedback)
            console.print(
                "[dim]Waiting for Jules to process feedback (expecting IN_PROGRESS)...[/dim]"
            )

            state_transitioned = False
            for attempt in range(12):
                await asyncio.sleep(5)
                current_state = await self.jules.get_session_state(session_id)
                console.print(f"[dim]State check ({attempt + 1}/12): {current_state}[/dim]")

                # Official Jules API active states (non-terminal)
                ACTIVE_STATES = {
                    "IN_PROGRESS",
                    "QUEUED",
                    "PLANNING",
                    "AWAITING_PLAN_APPROVAL",
                    "AWAITING_USER_FEEDBACK",
                    "PAUSED",
                    "COMPLETED",  # Jules may complete quickly before returning to IN_PROGRESS
                }
                if current_state in ACTIVE_STATES:
                    state_transitioned = True
                    console.print(
                        f"[green]Jules session is now active ({current_state}). Proceeding to monitor...[/green]"
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

            if result.get("status") == "success" or result.get("pr_url"):
                return {"status": FlowStatus.READY_FOR_AUDIT, "pr_url": result.get("pr_url")}

            console.print(
                "[yellow]Jules session finished without new PR. Creating new session...[/yellow]"
            )
            return None  # noqa: TRY300

        except Exception as e:
            console.print(
                f"[yellow]Failed to send feedback to existing session: {e}. Creating new session...[/yellow]"
            )
        return None

    async def execute_qa_session(self, state: CycleState) -> dict[str, Any]:  # noqa: C901, PLR0912, PLR0915
        """Node logic for QA Agent session."""
        console.print("[bold cyan]Starting QA Session (Tutorial Generation)...[/bold cyan]")

        docs_dir = settings.paths.documents_dir
        qa_instruction = settings.get_template("QA_TUTORIAL_INSTRUCTION.md").read_text()
        full_prompt = f"{qa_instruction}\n\nTask: Generate the tutorials based on Final UAT."

        files_to_send = []
        for file_name in ["USER_TEST_SCENARIO.md", "system_prompts/SYSTEM_ARCHITECTURE.md"]:
            file_path = docs_dir / file_name
            if file_path.exists():
                files_to_send.append(str(file_path))

        if (Path.cwd() / "pyproject.toml").exists():
            files_to_send.append(str(Path.cwd() / "pyproject.toml"))

        tutorials_dir = Path.cwd() / "tutorials"
        if tutorials_dir.exists():
            for py_file in tutorials_dir.glob("*.py"):
                files_to_send.append(str(py_file))

        try:
            mgr = StateManager()
            manifest = mgr.load_manifest()

            persistent_qa_id = manifest.qa_session_id if manifest else None
            memory_qa_id = state.jules_session_name
            session_id = state.project_session_id or settings.current_session_id
            qa_session_id = persistent_qa_id or memory_qa_id or f"qa-{session_id}"

            if state.status == FlowStatus.REJECTED and state.audit_result:
                current_retries = state.qa_retry_count
                if current_retries >= 5:
                    console.print(
                        f"[bold red]Max QA retries ({current_retries}) exceeded. Stopping loop.[/bold red]"
                    )
                    return {"status": FlowStatus.MAX_RETRIES, "error": "Max QA retries exceeded"}

                feedback = state.audit_result.feedback if state.audit_result else ""
                console.print(
                    f"[bold yellow]Sending Audit Feedback to Existing QA Session: {qa_session_id}... (Retry {current_retries + 1}/5)[/bold yellow]"
                )

                feedback_template = settings.get_template("AUDIT_FEEDBACK_MESSAGE.md").read_text()
                feedback_msg = str(feedback_template).replace("{{feedback}}", str(feedback))
                result = await self._send_audit_feedback_to_session(
                    session_id=qa_session_id,
                    feedback=feedback_msg,
                )

                next_retries = current_retries + 1

                if result:
                    return {
                        "status": FlowStatus.READY_FOR_AUDIT,
                        "pr_url": result.get("pr_url"),
                        "jules_session_name": qa_session_id,
                        "qa_retry_count": next_retries,
                    }

                console.print(
                    "[yellow]Could not reuse session. Starting new session with feedback...[/yellow]"
                )
                import re

                injection_template = str(
                    settings.get_template("AUDIT_FEEDBACK_INJECTION.md").read_text()
                )
                injection = injection_template.replace("{{feedback}}", str(feedback))
                injection = str(
                    re.sub(r"\{\{#pr_url\}\}.*?\{\{/pr_url\}\}", "", injection, flags=re.DOTALL)
                ).strip()
                full_prompt += f"\n\n{injection}"
                qa_session_id = f"qa-{session_id}"
                state.qa_retry_count = next_retries

            result = await self.jules.run_session(
                session_id=qa_session_id,
                prompt=full_prompt,
                files=files_to_send,
                require_plan_approval=False,
            )

            real_session_name = result.get("session_name") or qa_session_id

            if mgr and real_session_name:
                try:
                    mgr.update_project_state(qa_session_id=real_session_name)
                    console.print(f"[dim]Persisted QA Session ID: {real_session_name}[/dim]")
                except Exception as e:
                    console.print(f"[red]Failed to persist QA Session ID: {e}[/red]")

            ret_dict = {
                "jules_session_name": real_session_name,
                "qa_retry_count": state.qa_retry_count,
            }

            if result.get("pr_url"):
                ret_dict.update({"status": FlowStatus.READY_FOR_AUDIT, "pr_url": result["pr_url"]})
                return ret_dict

            if result.get("status") == "success":
                ret_dict["status"] = FlowStatus.READY_FOR_AUDIT
                return ret_dict

            return {"status": FlowStatus.FAILED, "error": "jules failed to produce tutorials"}  # noqa: TRY300

        except Exception as e:
            return {"status": FlowStatus.FAILED, "error": str(e)}

    async def execute_qa_audit(self, state: CycleState) -> dict[str, Any]:  # noqa: C901, PLR0912, PLR0915
        """Node for QA Auditor (Reviewing Tutorials)."""
        console.print("[bold magenta]Starting QA Auditor...[/bold magenta]")

        instruction = settings.get_template("QA_AUDITOR_INSTRUCTION.md").read_text()

        docs_dir = settings.paths.documents_dir
        context_files = {}
        for fname in ["USER_TEST_SCENARIO.md", "system_prompts/SYSTEM_ARCHITECTURE.md"]:
            p = docs_dir / fname
            if p.exists():
                context_files[fname] = p.read_text(encoding="utf-8")

        pr_url = state.pr_url

        if pr_url:
            try:
                await self.git.checkout_pr(pr_url)
                console.print(f"[dim]Checked out PR: {pr_url}[/dim]")
            except Exception as e:
                console.print(f"[yellow]Failed to checkout PR: {e}. using current files.[/yellow]")

        tutorials_dir = Path.cwd() / "tutorials"
        target_files = {}
        if tutorials_dir.exists():
            for py_file in tutorials_dir.glob("*.py"):
                target_files[f"tutorials/{py_file.name}"] = py_file.read_text(encoding="utf-8")

        if not target_files:
            console.print("[red]No tutorials found to audit![/red]")
            return {"status": FlowStatus.FAILED, "error": "No tutorials generated"}

        import json

        import litellm
        from langchain_core.utils.function_calling import convert_to_openai_tool

        async with self.mcp_client as client:
            tools = await client.get_tools(server_name="e2b")
            litellm_tools = [convert_to_openai_tool(t) for t in tools]
            tools_map = {t.name: t for t in tools}

            prompt = f"{instruction}\n\nHere are the target files:\n"
            for k, v in target_files.items():
                prompt += f"\n--- {k} ---\n{v}\n"
            prompt += "\n\nHere are the context docs:\n"
            for k, v in context_files.items():
                prompt += f"\n--- {k} ---\n{v}\n"
            prompt += "\n\nYou MUST use the 'run_code' tool to execute the tutorials before providing your final JSON review!"

            messages = [
                {"role": "system", "content": "You are a QA Auditor. Use tools to verify code execution, then output valid JSON AuditorReport."},
                {"role": "user", "content": prompt}
            ]

            response = await litellm.acompletion(
                model=settings.reviewer.fast_model,
                messages=messages,
                tools=litellm_tools,
                temperature=0.0
            )

            message = response.choices[0].message

            # If the LLM called tools, execute them and feed them back
            if message.tool_calls:
                messages.append(message.model_dump())
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    selected_tool = tools_map.get(tool_name)
                    if selected_tool:
                        tool_result = await selected_tool.ainvoke(tool_args)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": str(tool_result)
                        })
                    else:
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": f"Error: Tool {tool_name} not found"
                        })

                # Ask LLM to generate the final JSON review
                response = await litellm.acompletion(
                    model=settings.reviewer.fast_model,
                    messages=messages,
                    temperature=0.0
                )
                message = response.choices[0].message

            audit_feedback = message.content or ""

            # Extract JSON from potential markdown wrapping
            if "```json" in audit_feedback:
                audit_feedback = audit_feedback.split("```json")[1].split("```")[0].strip()
            elif "```" in audit_feedback:
                audit_feedback = audit_feedback.split("```")[1].split("```")[0].strip()

            # We must map the JSON response to REVIEW_PASSED or REVIEW_FAILED manually
            # Since LLMReviewer does this, we simulate its formatting
            try:
                from src.domain_models import AuditorReport
                report = AuditorReport.model_validate_json(audit_feedback)
                if report.is_passed:
                    audit_feedback = "-> REVIEW_PASSED\n\n" + audit_feedback
                else:
                    audit_feedback = "-> REVIEW_FAILED\n\n" + audit_feedback
            except Exception as e:
                audit_feedback = f"-> REVIEW_FAILED\n\nParse Error: {e}"


        status = FlowStatus.APPROVED
        if "-> REVIEW_PASSED" in audit_feedback:
            status = FlowStatus.APPROVED
        elif "-> REVIEW_FAILED" in audit_feedback:
            status = FlowStatus.REJECTED
        else:
            status = FlowStatus.REJECTED

        result = AuditResult(
            status=status.upper(),
            is_approved=(status == FlowStatus.APPROVED),
            reason="QA Audit Complete",
            feedback=audit_feedback,
        )

        console.print(
            Panel(
                f"Status: {status}\nReason: {result.reason}",
                title="QA Audit Result",
                border_style="green" if status == FlowStatus.APPROVED else "red",
            )
        )

        return {
            "audit_result": result,
            "status": status,
        }
