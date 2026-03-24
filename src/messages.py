"""Centralized error messages with recovery instructions."""

import sys

from rich.console import Console
from rich.panel import Panel

from src.utils import check_api_key, get_command_prefix


class RecoveryMessages:
    """Provides consistent error messages with actionable recovery steps."""

    @staticmethod
    def session_not_found() -> str:
        """Error message when no session can be found."""
        cmd = get_command_prefix()
        return (
            "No active session found.\n\n"
            "Recovery Options:\n"
            "1. Start a completely new session:\n"
            f"   {cmd} gen-cycles\n"
            "2. Resume an existing session by ID:\n"
            f"   {cmd} run-pipeline --session <session-id>"
        )

    @staticmethod
    def merge_failed(pr_url: str, next_step: str) -> str:
        """Error message when auto-merge fails."""
        return (
            f"Auto-merge failed.\n\n"
            f"The PR was created but could not be automatically merged into the integration branch.\n"
            f"Please review and merge it manually: {pr_url}\n\n"
            f"After merging, resume automation with:\n"
            f"   {next_step}"
        )

    @staticmethod
    def architect_merge_failed(pr_url: str) -> str:
        """Error message when architect PR merge fails."""
        cmd = get_command_prefix()
        return RecoveryMessages.merge_failed(pr_url, f"{cmd} run-pipeline")

    @staticmethod
    def cycle_merge_failed(pr_url: str) -> str:
        """Error message when cycle PR merge fails."""
        cmd = get_command_prefix()
        return RecoveryMessages.merge_failed(pr_url, f"{cmd} run-pipeline")

    @staticmethod
    def branch_not_found(branch: str, session_file: str = ".nitpick_session.json") -> str:
        """Error message when integration branch doesn't exist."""
        cmd = get_command_prefix()
        return (
            f"Integration branch '{branch}' does not exist locally.\n\n"
            f"Recovery Options:\n"
            f"1. Fetch the branch from remote and retry:\n"
            f"   git fetch origin {branch}:{branch} && {cmd} run-pipeline\n"
            f"2. Restart the session if the branch was deleted:\n"
            f"   rm {session_file} && {cmd} gen-cycles"
        )

    @staticmethod
    def remote_branch_missing(branch: str) -> str:
        """Warning when branch exists locally but not on remote."""
        cmd = get_command_prefix()
        return (
            f"Integration branch '{branch}' exists locally but not on remote.\n\n"
            f"Recovery Action:\n"
            f"1. Push the branch to remote and resume:\n"
            f"   git push -u origin {branch} && {cmd} run-pipeline"
        )

    @staticmethod
    def merge_conflict(source: str, target: str, original_branch: str) -> str:
        """Error message with merge conflict recovery steps."""
        cmd = get_command_prefix()
        return (
            f"Merge conflict detected between {source} and {target}.\n\n"
            f"Recovery Options:\n"
            f"1. Let the automated Master Integrator resolve this (Recommended):\n"
            f"   {cmd} run-pipeline\n\n"
            f"2. Resolve conflicts manually:\n"
            f"   git checkout {target}\n"
            f"   git merge {source}\n"
            f"   # Fix conflicts, commit, and then resume:\n"
            f"   {cmd} run-pipeline\n\n"
            f"3. Abandon merge and return to original branch:\n"
            f"   git merge --abort && git checkout {original_branch}"
        )


class SuccessMessages:
    """Centralized success messages with next steps."""

    @staticmethod
    def architect_complete(session_id: str, integration_branch: str) -> str:
        """Success message for architect phase completion."""
        cmd = get_command_prefix()
        return (
            f"✅ Phase 1: Architect Complete! (Session: {session_id})\n\n"
            f"Architecture blueprints are ready on branch: {integration_branch}\n\n"
            "Recommended Next Step (Fully Automated E2E):\n"
            f"   {cmd} run-pipeline\n\n"
            "Alternative Next Step (Run Phase 2 Parallel Cycles):\n"
            f"   {cmd} run-cycle --id all --parallel"
        )

    @staticmethod
    def cycle_complete(cycle_id: str, next_cycle_id: str | None = None) -> str:
        """Success message for cycle completion."""
        cmd = get_command_prefix()
        if next_cycle_id:
            return (
                f"✅ Phase 2: Coder Cycle {cycle_id} Complete!\n\n"
                "Next Step:\n"
                f"   {cmd} run-cycle --id {next_cycle_id}"
            )
        return (
            f"✅ Phase 2: Coder Cycle {cycle_id} Complete!\n\n"
            "All cycles have been implemented.\n\n"
            "Next Step (Start Phases 3 & 4 - Integration and UAT):\n"
            f"   {cmd} run-pipeline"
        )

    @staticmethod
    def all_cycles_complete() -> str:
        """Success message for all cycles completion (Phase 2 parallel)."""
        cmd = get_command_prefix()
        return (
            "✅ Phase 2: All Parallel Cycles Complete!\n\n"
            "Next Step (Start Phases 3 & 4 - Integration and UAT):\n"
            f"   {cmd} run-pipeline"
        )

    @staticmethod
    def pipeline_complete() -> str:
        """Success message for pipeline completion."""
        cmd = get_command_prefix()
        return (
            "✅ Phase 4: Pipeline Verification Complete!\n\n"
            "All cycles are integrated and verified successfully.\n\n"
            "Next Step (Create Final PR):\n"
            f"   {cmd} finalize-session"
        )

    @staticmethod
    def session_finalized(pr_url: str) -> str:
        """Success message for session finalization."""
        cmd = get_command_prefix()
        return (
            f"✅ Phase 5: Finalization Complete!\n\n"
            f"Final PR created and ready for human review: {pr_url}\n\n"
            "Next Steps:\n"
            "1. Review and Merge the PR on GitHub\n"
            "2. The integration branch will be automatically deleted upon merge.\n\n"
            "To start a new session, run:\n"
            f"   {cmd} gen-cycles"
        )

    @staticmethod
    def show_panel(message: str, title: str = "Next Action Guide") -> None:
        """Display message in a styled panel."""
        cons = Console()
        cons.print(Panel(message, title=title, style="bold green", expand=False))


def ensure_api_key() -> None:
    """Check API key availability and exit if missing."""
    cons = Console()
    try:
        check_api_key()
    except ValueError as e:
        cons.print(f"[red]Configuration Error:[/red] {e}")
        sys.exit(1)
