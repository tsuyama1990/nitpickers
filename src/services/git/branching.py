from src.utils import logger

from .base import BaseGitManager


class GitBranchingMixin(BaseGitManager):
    """Mixin for Git branching logic."""

    async def get_current_branch(self) -> str:
        try:
            return await self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        except RuntimeError:
            return "main"

    async def get_remote_url(self) -> str:
        """Returns the URL of the 'origin' remote."""
        return await self._run_git(["config", "--get", "remote.origin.url"])

    async def create_working_branch(self, prefix: str, branch_id: str) -> str:
        """
        Creates and checks out a feature branch: feature/{prefix}-{branch_id}.
        """
        branch_name = f"feature/{prefix}-{branch_id}"
        logger.info(f"Switching to branch {branch_name}...")

        # Check if branch exists
        _stdout, _stderr, code, _ = await self.runner.run_command(
            [self.git_cmd, "rev-parse", "--verify", branch_name], check=False
        )

        if code == 0:
            logger.info(f"Branch {branch_name} exists. Checking out...")
            await self._run_git(["checkout", branch_name])
        else:
            logger.info(f"Branch does not exist. Creating {branch_name}...")
            await self._run_git(["checkout", "-b", branch_name])

        return branch_name

    async def _auto_commit_if_dirty(self, message: str = "Auto-save before branch switch") -> None:
        """Automatically commits changes if the working directory is dirty."""
        # Check for uncommitted changes
        stdout, _stderr, _code, _ = await self.runner.run_command(
            [self.git_cmd, "status", "--porcelain"], check=False
        )
        if stdout.strip():
            # CRITICAL: Check for unresolved conflicts before committing
            # Git porcelain v1 conflict codes: DD, AU, UD, UA, DU, AA, UU
            lines = stdout.splitlines()
            from src.config import settings

            conflict_codes = settings.tools.conflict_codes
            for line in lines:
                if line[:2] in conflict_codes:
                    error_msg = (
                        f"Cannot auto-commit due to unresolved conflicts: {line[3:]}. "
                        "Please resolve conflicts before proceeding."
                    )
                    raise RuntimeError(error_msg)

            logger.info("Uncommitted changes detected. Auto-committing...")
            await self._run_git(["add", "."])
            await self._run_git(["commit", "-m", message])
            logger.info("✓ Auto-committed changes.")

    async def create_integration_branch(
        self, session_id: str, prefix: str = "dev", branch_name: str | None = None
    ) -> str:
        """Creates integration branch from main for the session."""
        integration_branch = branch_name if branch_name else f"{prefix}/{session_id}/integration"
        logger.info(f"Creating integration branch: {integration_branch}")

        await self._auto_commit_if_dirty()

        await self._run_git(["checkout", "main"])
        await self._run_git(["pull"])

        _stdout, _stderr, code, _ = await self.runner.run_command(
            [self.git_cmd, "rev-parse", "--verify", integration_branch], check=False
        )

        if code == 0:
            logger.info(f"Integration branch {integration_branch} exists. Checking out...")
            await self._run_git(["checkout", integration_branch])
            try:
                await self._run_git(["pull"])
            except Exception as e:
                logger.warning(f"Pull failed on existing branch (perhaps no upstream): {e}")
                logger.info(f"Attempting to push {integration_branch} to origin...")
                try:
                    await self._run_git(["push", "-u", "origin", integration_branch])
                except Exception as push_err:
                    logger.error(f"Failed to push existing branch: {push_err}")
        else:
            logger.info(f"Creating new integration branch: {integration_branch}")
            await self._run_git(["checkout", "-b", integration_branch])
            await self._run_git(["push", "-u", "origin", integration_branch])

        return integration_branch

    async def create_feature_branch(self, branch_name: str, from_branch: str | None = None) -> str:
        print("MOCKED create_feature_branch INJECTED")
        await self._auto_commit_if_dirty()
        await self._run_git(["checkout", "-B", branch_name])
        return branch_name

