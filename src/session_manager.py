"""Session management utilities for AC-CDD using Git-based state persistence."""

import json
from datetime import UTC, datetime
from typing import Any

from src.domain_models import CycleManifest, ProjectManifest
from src.utils import logger


class SessionValidationError(Exception):
    """Raised when session validation fails."""


class SessionManager:
    """
    Manages session persistence using a unified project manifest stored in an orphan branch.
    No local state files are used.
    """

    STATE_FILE = "project_state.json"

    STATE_BRANCH = "ac-cdd/state"

    def __init__(self) -> None:
        from src.process_runner import ProcessRunner
        self.runner = ProcessRunner()

    async def _read_state_file(self) -> str | None:
        try:
            _stdout, _stderr, code, _ = await self.runner.run_command(
                ["git", "show", f"{self.STATE_BRANCH}:{self.STATE_FILE}"], check=False
            )
            if code == 0:
                return _stdout.strip()
        except Exception as e:
            logger.debug(f"Could not read state file: {e}")
        return None

    async def _save_state_file(self, content: str, commit_msg: str) -> None:
        try:
            _stdout, _stderr, _code, _ = await self.runner.run_command(
                ["git", "branch", "--list", self.STATE_BRANCH], check=False
            )
            if not _stdout.strip():
                # create orphan branch
                await self.runner.run_command(["git", "checkout", "--orphan", self.STATE_BRANCH], check=True)
                await self.runner.run_command(["git", "rm", "-rf", "."], check=True)

            # Use worktree to safely modify the state branch without destroying working dir
            import tempfile
            from pathlib import Path

            import anyio
            with tempfile.TemporaryDirectory() as tmp_dir:
                await self.runner.run_command(["git", "worktree", "add", "-f", tmp_dir, self.STATE_BRANCH], check=True)
                file_path = Path(tmp_dir) / self.STATE_FILE
                await anyio.Path(file_path).write_text(content, encoding="utf-8")
                await self.runner.run_command(["git", "-C", tmp_dir, "add", self.STATE_FILE], check=True)
                await self.runner.run_command(["git", "-C", tmp_dir, "commit", "-m", commit_msg], check=True)
                await self.runner.run_command(["git", "worktree", "remove", "-f", tmp_dir], check=True)
        except Exception as e:
            logger.warning(f"Could not save state file natively: {e}")

    async def load_manifest(self) -> ProjectManifest | None:
        """Loads manifest from the orphan state branch."""
        content = await self._read_state_file()
        if not content:
            return None

        try:
            data = json.loads(content)
            return ProjectManifest(**data)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Failed to load project manifest: {e}")
            return None

    async def save_manifest(
        self, manifest: ProjectManifest, commit_msg: str = "Update state"
    ) -> None:
        """Saves manifest to the orphan state branch."""
        try:
            manifest.last_updated = datetime.now(UTC)
            content = manifest.model_dump_json(indent=2)
            await self._save_state_file(content, commit_msg)
        except Exception as e:
            logger.exception(f"Failed to save manifest: {e}")
            raise

    async def create_manifest(
        self, project_session_id: str, feature_branch: str, integration_branch: str
    ) -> ProjectManifest:
        """Creates and saves a new project manifest."""
        manifest = ProjectManifest(
            project_session_id=project_session_id,
            feature_branch=feature_branch,
            integration_branch=integration_branch,
        )
        await self.save_manifest(
            manifest, commit_msg=f"Initialize project state for session {project_session_id}"
        )
        return manifest

    async def get_cycle(self, cycle_id: str) -> CycleManifest | None:
        """Helper to get a specific cycle from the manifest."""
        manifest = await self.load_manifest()
        if not manifest:
            return None

        for cycle in manifest.cycles:
            if cycle.id == cycle_id:
                return cycle
        return None

    async def update_cycle_state(self, cycle_id: str, **kwargs: Any) -> None:
        """
        Updates specific fields of a cycle and saves the manifest immediately.

        Example: await update_cycle_state("01", status="in_progress", jules_session_id="...")
        """
        manifest = await self.load_manifest()
        if not manifest:
            msg = "No active project manifest found."
            raise SessionValidationError(msg)

        cycle = next((c for c in manifest.cycles if c.id == cycle_id), None)
        if not cycle:
            msg = f"Cycle {cycle_id} not found in manifest."
            raise SessionValidationError(msg)

        updated = False
        for key, value in kwargs.items():
            if hasattr(cycle, key):
                setattr(cycle, key, value)
                updated = True

        if updated:
            cycle.updated_at = datetime.now(UTC)
            commit_msg = f"Update cycle {cycle_id}"
            if "status" in kwargs:
                commit_msg += f" status to {kwargs['status']}"
            if "jules_session_id" in kwargs:
                commit_msg += " (Session ID updated)"

            await self.save_manifest(manifest, commit_msg=commit_msg)

    @staticmethod
    async def clear_session() -> None:
        """
        In the orphan branch model, clearing session might mean deleting the file or resetting it.
        For now, we will leave it as manual git operation or implementation if needed.
        Typically we don't delete history in this model, but we might mark as archived.
        """
        # Implementation for clearing state if strictly required,
        # but usually we just start a new session which overwrites or creates new.
