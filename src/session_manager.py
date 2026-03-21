"""Session management utilities for AC-CDD using Git-based state persistence."""

from datetime import UTC, datetime
from typing import Any

from src.domain_models import CycleManifest, ProjectManifest


class SessionValidationError(Exception):
    """Raised when session validation fails."""


class SessionManager:
    """
    Deprecated class. Use StateManager in state_manager.py instead.
    """

    STATE_FILE = "project_state.json"

    def __init__(self) -> None:
        pass

    async def load_manifest(self) -> ProjectManifest | None:
        msg = "SessionManager is deprecated. Use StateManager."
        raise NotImplementedError(msg)

    async def save_manifest(
        self, manifest: ProjectManifest, commit_msg: str = "Update state"
    ) -> None:
        msg = "SessionManager is deprecated. Use StateManager."
        raise NotImplementedError(msg)

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
