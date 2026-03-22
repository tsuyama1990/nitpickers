import asyncio
import re
from datetime import UTC, datetime
from typing import Any

from rich.console import Console

from src.config import settings
from src.domain_models import CycleManifest
from src.enums import FlowStatus, WorkPhase
from src.services.jules_client import JulesClient
from src.state import CycleState
from src.state_manager import StateManager

console = Console()

# Jules API states that mean "session is still active/in-flight"
_ACTIVE_STATES = {
    "IN_PROGRESS",
    "QUEUED",
    "PLANNING",
    "AWAITING_PLAN_APPROVAL",
    "AWAITING_USER_FEEDBACK",
    "PAUSED",
}

# Jules API states where an existing session can receive new messages
_REUSABLE_STATES = {"IN_PROGRESS", "COMPLETED", "AWAITING_USER_FEEDBACK", "PAUSED"}


class CoderUseCase:
    """
    Encapsulates the logic and interactions with the Coder AI (Jules).
    """

    def __init__(self, jules_client: JulesClient) -> None:
        if not jules_client:
            msg = "JulesClient must be injected into CoderUseCase"
            raise ValueError(msg)
        self.jules = jules_client

    # ------------------------------------------------------------------ #
    #  Public entry point                                                  #
    # ------------------------------------------------------------------ #

    async def execute(self, state: CycleState) -> dict[str, Any]:  # noqa: C901
        """Routes the coder session through its many possible modes."""
        cycle_id = state.cycle_id
        iteration = state.iteration_count
        current_phase = state.current_phase
        phase_label = "REFACTORING" if current_phase == WorkPhase.REFACTORING else "CODER"

        mgr = StateManager()
        cycle_manifest = mgr.get_cycle(cycle_id)

        jules_session_name: str | None = None
        result: dict[str, Any] | None = None

        # --- A. Attempt to identify/wait for an EXISTING session ---
        if (
            state.status == FlowStatus.WAIT_FOR_JULES_COMPLETION
            or (state.resume_mode and state.status != FlowStatus.RETRY_FIX)
        ) and (cycle_manifest and cycle_manifest.jules_session_id):
            jules_session_name = cycle_manifest.jules_session_id
            console.print(
                f"[bold blue]Waiting/Resuming Jules Session: {jules_session_name}[/bold blue]"
            )
            try:
                result = await self.jules.wait_for_completion(jules_session_name)
                if not (result.get("status") == "success" or result.get("pr_url")):
                    console.print(
                        "[yellow]Existing session did not produce PR. Restarting...[/yellow]"
                    )
                    result = None
            except Exception as e:
                console.print(f"[yellow]Wait/Resume failed: {e}. Starting new session.[/yellow]")
                result = None

        # --- B. Handle session REUSE (Retry Fix or Post-Audit Refactor) ---
        if not result and state.status in {FlowStatus.RETRY_FIX, FlowStatus.POST_AUDIT_REFACTOR}:
            result = await self._try_reuse_session(cycle_manifest, state)
            if result:
                # _try_reuse_session returns FlowStatus dict, not raw Jules result
                # but we need the session name for potential Critic (though Critic is skipped on retry)
                jules_session_name = cycle_manifest.jules_session_id if cycle_manifest else None
                # If reuse failed, result is None, falling through to New Session

        # --- C. Launch NEW session ---
        if not result:
            console.print(
                f"[bold green]Starting {phase_label} Session for Cycle {cycle_id} "
                f"(Iteration {iteration})...[/bold green]"
            )
            instruction = self._build_instruction(cycle_id, current_phase, state, cycle_manifest)
            target_files = settings.get_target_files()
            context_files = settings.get_context_files()

            try:
                timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M")
                prefix = "refactor" if current_phase == WorkPhase.REFACTORING else "coder"
                session_req_id = f"{prefix}-cycle-{cycle_id}-iter-{iteration}-{timestamp}"

                jules_session_name, result = await self._run_jules_session(
                    session_req_id, instruction, target_files, context_files, cycle_id, mgr
                )
            except Exception as e:
                console.print(f"[red]{phase_label} Session Failed: {e}[/red]")
                return self._handle_session_failure(cycle_manifest, cycle_id, str(e), mgr)

        # --- D. Post-Session Processing (Success Handling & Self-Critic) ---
        if result and (result.get("status") == "success" or result.get("pr_url")):
            # Self-Critic phase: initial PR only OR post-audit refactor
            # CRITICAL: This triggers for the very first PR in a cycle AND the final polish PR.
            is_initial_pr = iteration <= 1 and state.status != FlowStatus.RETRY_FIX
            is_post_audit_refactor = state.status == FlowStatus.POST_AUDIT_REFACTOR

            if (is_initial_pr or is_post_audit_refactor) and jules_session_name:
                result = await self._run_critic_phase(cycle_id, jules_session_name) or result

            if cycle_manifest:
                mgr.update_cycle_state(cycle_id, session_restart_count=0)

            # If we just finished a post-audit refactor, we are COMPLETED for this cycle
            if is_post_audit_refactor:
                return {"status": FlowStatus.COMPLETED, "pr_url": result.get("pr_url")}

            return {"status": FlowStatus.READY_FOR_AUDIT, "pr_url": result.get("pr_url")}

        # --- E. Failure Handling ---
        if result and result.get("status") == "failed":
            return self._handle_session_failure(
                cycle_manifest, cycle_id, result.get("error", "Unknown error"), mgr
            )

        return {"status": FlowStatus.FAILED, "error": "Jules failed to produce PR"}

    def _build_instruction(
        self,
        cycle_id: str,
        current_phase: WorkPhase | str | None,
        state: CycleState,
        cycle_manifest: CycleManifest | None,
    ) -> str:
        """Assemble the Jules instruction prompt, injecting feedback when retrying."""
        if state.status == FlowStatus.POST_AUDIT_REFACTOR:
            instruction = settings.get_prompt_content(
                settings.template_files.post_audit_refactor_instruction
            )
        elif current_phase == WorkPhase.REFACTORING:
            instruction = settings.get_prompt_content(
                settings.template_files.final_refactor_instruction
            )
        else:
            instruction = settings.get_prompt_content(settings.template_files.coder_instruction)

        if not instruction:
            instruction = "Implement the requested changes."

        instruction = instruction.replace("{{cycle_id}}", str(cycle_id))

        last_audit = state.audit_result
        if state.status == FlowStatus.RETRY_FIX and last_audit and last_audit.feedback:
            instruction += "\n\n" + self._build_feedback_injection(
                last_audit.feedback, cycle_manifest.pr_url if cycle_manifest else None
            )

        if state.status == FlowStatus.RETRY_FIX and state.current_fix_plan:
            fix_plan_text = (
                f"## Automated UAT Diagnostic Fix Plan\n"
                f"A recent execution failure was diagnosed by the Outer Loop Auditor.\n"
                f"**Defect Description:** {state.current_fix_plan.defect_description}\n\n"
            )
            for patch in state.current_fix_plan.patches:
                fix_plan_text += (
                    f"**Target File:** `{patch.target_file}`\n"
                    f"**Required Changes:**\n```\n{patch.git_diff_patch}\n```\n\n"
                )
            fix_plan_text += "Please implement these exact changes immediately."
            instruction += "\n\n" + self._build_feedback_injection(
                fix_plan_text, cycle_manifest.pr_url if cycle_manifest else None
            )

        return str(instruction)

    async def _try_reuse_session(
        self, cycle_manifest: CycleManifest | None, state: CycleState
    ) -> dict[str, Any] | None:
        """Attempt to send audit feedback to an existing session instead of starting fresh."""
        cycle_id = state.cycle_id
        last_audit = state.audit_result
        # Reuse for Retry Fix (Audit failed) OR Post-Audit Refactor (Audit passed) OR UAT Fix Plan
        is_retry_audit = state.status == FlowStatus.RETRY_FIX and last_audit and last_audit.feedback
        is_retry_uat = state.status == FlowStatus.RETRY_FIX and state.current_fix_plan
        is_post_refactor = state.status == FlowStatus.POST_AUDIT_REFACTOR

        if not (
            (is_retry_audit or is_retry_uat or is_post_refactor)
            and cycle_manifest
            and cycle_manifest.jules_session_id
        ):
            return None

        session_state = await self.jules.get_session_state(cycle_manifest.jules_session_id)
        if session_state not in _REUSABLE_STATES:
            console.print(
                f"[yellow]Session in unexpected/failed state ({session_state}). "
                f"Creating new session...[/yellow]"
            )
            return None

        console.print(
            f"[dim]Reusing session ({session_state}) for final polish: {cycle_manifest.jules_session_id}[/dim]"
        )
        # For Post-Audit Refactor, we send the new instruction as a message
        if state.status == FlowStatus.POST_AUDIT_REFACTOR:
            instruction = self._build_instruction(cycle_id, None, state, cycle_manifest)
            if cycle_manifest.jules_session_id is not None:
                return await self._send_audit_feedback_to_session(
                    cycle_manifest.jules_session_id, instruction
                )
            return {
                "status": FlowStatus.FAILED,
                "error": "No jules_session_id available for POST_AUDIT_REFACTOR.",
            }

        if cycle_manifest.jules_session_id is not None:
            feedback_payload = ""
            if is_retry_audit and last_audit and last_audit.feedback:
                feedback_payload = last_audit.feedback
            elif is_retry_uat and state.current_fix_plan:
                feedback_payload = (
                    f"## Automated UAT Diagnostic Fix Plan\n"
                    f"A recent execution failure was diagnosed by the Outer Loop Auditor.\n"
                    f"**Defect Description:** {state.current_fix_plan.defect_description}\n\n"
                )
                for patch in state.current_fix_plan.patches:
                    feedback_payload += (
                        f"**Target File:** `{patch.target_file}`\n"
                        f"**Required Changes:**\n```\n{patch.git_diff_patch}\n```\n\n"
                    )
                feedback_payload += "Please implement these exact changes immediately."

            return await self._send_audit_feedback_to_session(
                cycle_manifest.jules_session_id, feedback_payload
            )
        return {"status": FlowStatus.FAILED, "error": "No jules_session_id available."}

    async def _run_jules_session(
        self,
        session_req_id: str,
        instruction: str,
        target_files: list[str],
        context_files: list[str],
        cycle_id: str,
        mgr: StateManager,
    ) -> tuple[str | None, dict[str, Any]]:
        """Launch a new Jules session and wait for it to complete.

        Returns (jules_session_name, result_dict). The session_name is saved
        separately so it survives the wait_for_completion() result overwrite.
        """
        if not re.match(r"^[A-Za-z0-9_-]+$", session_req_id):
            msg = f"Invalid session_req_id format: {session_req_id}"
            raise ValueError(msg)

        result = await self.jules.run_session(
            session_id=session_req_id,
            prompt=instruction,
            target_files=target_files,
            context_files=context_files,
            require_plan_approval=False,
        )

        # Capture session_name BEFORE wait_for_completion() overwrites result —
        # wait_for_completion() does NOT include session_name in its return value.
        jules_session_name: str | None = result.get("session_name")

        if jules_session_name:
            mgr.update_cycle_state(
                cycle_id, jules_session_id=jules_session_name, status="in_progress"
            )

        if result.get("status") == "running" and jules_session_name:
            console.print(
                f"[bold blue]Session {jules_session_name} created. Waiting for completion...[/bold blue]"
            )
            result = await self.jules.wait_for_completion(jules_session_name)

        return jules_session_name, result

    async def _run_critic_phase(
        self, cycle_id: str, jules_session_name: str
    ) -> dict[str, Any] | None:
        """Send CODER_CRITIC_INSTRUCTION to Jules and wait for the revised PR.

        Returns the updated result dict, or None if the phase should be skipped.
        """
        console.print(
            "[bold cyan]Initial Coder PR created. "
            "Invoking Coder Critic for self-reflection before Auditor review...[/bold cyan]"
        )
        try:
            critic_instruction = settings.get_prompt_content(
                settings.template_files.coder_critic_instruction
            )
            if not critic_instruction:
                console.print("[red]Failed to load Coder Critic instruction template.[/red]")
                console.print(
                    "[yellow]Warning: Coder Critic template missing, skipping self-reflection...[/yellow]"
                )
                return None

            critic_instruction = critic_instruction.replace("{{cycle_id}}", str(cycle_id))

            session_url = self.jules._get_session_url(jules_session_name)
            await self.jules._send_message(session_url, critic_instruction)

            console.print("[dim]Waiting for Coder Critic to finish review and push fixes...[/dim]")
            await asyncio.sleep(10)

            return dict(await self.jules.wait_for_completion(jules_session_name))
        except Exception as e:
            console.print(f"[yellow]Warning: Coder Critic phase error, proceeding: {e}[/yellow]")
            return None

    async def _send_audit_feedback_to_session(
        self, session_id: str, feedback: str
    ) -> dict[str, Any] | None:
        """Send audit feedback to existing Jules session and wait for new PR.

        Returns result dict if successful, None if should create new session.
        """
        console.print(
            f"[bold yellow]Sending Audit Feedback to existing Jules session: {session_id}[/bold yellow]"
        )
        try:
            from src.utils_sanitization import sanitize_for_llm

            feedback_template = settings.get_prompt_content(
                settings.template_files.audit_feedback_message
            )
            if not feedback_template:
                feedback_template = "{{feedback}}"

            safe_feedback = sanitize_for_llm(feedback)
            feedback_msg = feedback_template.replace("{{feedback}}", safe_feedback)

            await self.jules._send_message(self.jules._get_session_url(session_id), feedback_msg)

            console.print(
                "[dim]Waiting for Jules to process feedback (expecting IN_PROGRESS)...[/dim]"
            )

            state_transitioned = False
            max_retries = settings.jules.feedback_wait_retries
            wait_interval = settings.jules.feedback_wait_interval_seconds

            for attempt in range(max_retries):
                await asyncio.sleep(wait_interval)
                current_state = await self.jules.get_session_state(session_id)
                console.print(
                    f"[dim]State check ({attempt + 1}/{max_retries}): {current_state}[/dim]"
                )

                if current_state in _ACTIVE_STATES:
                    state_transitioned = True
                    console.print(
                        f"[green]Jules session is now active ({current_state}). Proceeding to monitor...[/green]"
                    )
                    break
                if current_state == "FAILED":
                    console.print("[red]Jules session failed during feedback wait.[/red]")
                    return None
                if current_state == "COMPLETED":
                    console.print("[green]Jules session completed quickly.[/green]")
                    state_transitioned = True
                    break

            if not state_transitioned:
                console.print(
                    "[yellow]Warning: Jules session state did not change to IN_PROGRESS after 60s. "
                    "Assuming message received but state lagging, or task finished very quickly.[/yellow]"
                )

            result = await self.jules.wait_for_completion(session_id)
            if result.get("status") == "success" or result.get("pr_url"):
                return dict(result)

            console.print(
                "[yellow]Jules session finished without new PR. Creating new session...[/yellow]"
            )
            return None  # noqa: TRY300

        except Exception as e:
            console.print(
                f"[yellow]Failed to send feedback to existing session: {e}. Creating new session...[/yellow]"
            )
        return None

    # ------------------------------------------------------------------ #
    #  Utility helpers                                                     #
    # ------------------------------------------------------------------ #

    def _handle_session_failure(
        self, cycle_manifest: Any, cycle_id: str, error_msg: str, mgr: StateManager
    ) -> dict[str, Any]:
        """Handle session failures and manage restart counting."""
        if cycle_manifest:
            restart_count = cycle_manifest.session_restart_count
            max_restarts = cycle_manifest.max_session_restarts

            if restart_count < max_restarts:
                new_restart_count = restart_count + 1
                console.print(
                    f"[yellow]Restarting session (attempt {new_restart_count}/{max_restarts + 1})...[/yellow]"
                )
                mgr.update_cycle_state(
                    cycle_id,
                    jules_session_id=None,
                    session_restart_count=new_restart_count,
                    last_error=error_msg,
                )
                return {
                    "status": FlowStatus.CODER_RETRY,
                    "session_restart_count": new_restart_count,
                }

            console.print(
                f"[red]Max session restarts ({max_restarts}) reached. Failing cycle.[/red]"
            )

        return {"status": FlowStatus.FAILED, "error": error_msg}

    def _build_feedback_injection(self, feedback: str, pr_url: str | None) -> str:
        """Build feedback injection block from template."""
        template = str(
            settings.get_prompt_content(settings.template_files.audit_feedback_injection)
        )
        if not template:
            template = "{{feedback}}"
        result = template.replace("{{feedback}}", feedback)
        if pr_url:
            result = str(
                re.sub(
                    r"\{\{#pr_url\}\}\s*Previous PR: \{\{pr_url\}\}\s*\{\{/pr_url\}\}",
                    f"Previous PR: {pr_url}",
                    result,
                    flags=re.DOTALL,
                )
            )
        else:
            result = str(re.sub(r"\{\{#pr_url\}\}.*?\{\{/pr_url\}\}", "", result, flags=re.DOTALL))
        return result.strip()
