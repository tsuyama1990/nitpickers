with open('src/services/audit_orchestrator.py') as f:
    content = f.read()

content = content.replace('''from src.services.jules_client import JulesClient''', '''from src.services.mcp_client_manager import McpClientManager
from src.services.llm_reviewer import LLMReviewer
import json''')

content = content.replace('''    def __init__(
        self,
        jules_client: JulesClient,
        sandbox_runner: Any,
        plan_auditor: PlanAuditor | None = None,
    ) -> None:
        self.jules = jules_client
        if not self.jules:
            msg = "JulesClient must be injected into AuditOrchestrator"
            raise ValueError(msg)
        self.sandbox = sandbox_runner
        self.auditor = plan_auditor or PlanAuditor()''', '''    def __init__(
        self,
        mcp_client: McpClientManager | None = None,
        sandbox_runner: Any = None,
        plan_auditor: PlanAuditor | None = None,
        llm_reviewer: LLMReviewer | None = None,
    ) -> None:
        self.mcp_client = mcp_client or McpClientManager()
        self.sandbox = sandbox_runner
        self.auditor = plan_auditor or PlanAuditor()
        self.llm_reviewer = llm_reviewer or LLMReviewer()''')

content = content.replace('''        file_paths = list(spec_files.keys())

        session_data = await self.jules.run_session(
            session_id=settings.current_session_id,
            prompt=prompt,
            files=file_paths,
            require_plan_approval=True,
        )

        session_name = session_data["session_name"]
        console.print(f"[green]Session Created: {session_name}[/green]")

        retry_count = 0
        current_plan_id = None

        while retry_count <= max_retries:
            console.print(f"\\n[bold yellow]--- Audit Round {retry_count + 1} ---[/bold yellow]")
            console.print("[dim]Waiting for Jules to generate a plan...[/dim]")

            if current_plan_id:
                plan_details = await self._wait_for_new_plan(session_name, current_plan_id)
            else:
                activity = await self.jules.wait_for_activity_type(
                    session_name,
                    target_type="planGenerated",
                    timeout_seconds=300,
                )

                if not activity:
                    t_msg = "Timed out waiting for plan generation."
                    raise TimeoutError(t_msg)

                plan_details = activity.get("planGenerated", {})

            if not plan_details:
                v_msg = "Plan activity found but no details."
                raise ValueError(v_msg)

            plan_id = plan_details.get("planId")
            current_plan_id = plan_id
            console.print(f"[blue]Plan Generated (ID: {plan_id})[/blue]")

            audit_result = await self.auditor.audit_plan(
                plan_details, spec_files, phase="architect"
            )

            style = "green" if audit_result.status == "APPROVED" else "red"
            console.print(
                Panel(
                    f"Status: {audit_result.status}\\nReason: {audit_result.reason}",
                    title="Audit Result",
                    border_style=style,
                )
            )

            if audit_result.status == "APPROVED":
                console.print(
                    "[bold green]Plan Approved. Proceeding to implementation...[/bold green]"
                )
                if plan_id:
                    await self.jules.approve_plan(session_name, str(plan_id))
                result = await self.jules.wait_for_completion(session_name)
                return dict(result)

            retry_count += 1
            if retry_count > max_retries:
                console.print("[bold red]Max retries exceeded. Aborting session.[/bold red]")
                r_msg = "Max audit retries exceeded."
                raise RuntimeError(r_msg)

            feedback = audit_result.feedback or audit_result.reason
            feedback_prompt = (
                f"Your plan was REJECTED by the Lead Architect.\\n"
                f"Reason: {audit_result.reason}\\n"
                f"Instruction: {feedback}\\n"
                f"Please revise the plan accordingly."
            )

            console.print(f"[magenta]Sending Feedback to Jules:[/magenta] {feedback}")
            await self.jules.send_message(session_name, feedback_prompt)

        u_msg = "Session ended unexpectedly."
        raise RuntimeError(u_msg)''', '''        file_paths = list(spec_files.keys())

        # We will use MCP directly via llm_reviewer and mcp_client
        async with self.mcp_client as client:
            tools = await client.get_orchestration_tools(server_name="jules")
            model = settings.reviewer.smart_model

            orchestration_prompt = (
                "You are the Audit Orchestrator. Dispatch agents via Jules MCP to fulfill the following:\\n"
                f"{prompt}\\n\\n"
                f"Context files: {file_paths}\\n"
                "Use `create_session` and return the resulting diffs."
            )

            response = await self.llm_reviewer._ainvoke_with_tools(
                prompt=orchestration_prompt, model=model, tools=tools
            )

        return {"status": "success", "response": response}''')

with open('src/services/audit_orchestrator.py', 'w') as f:
    f.write(content)
