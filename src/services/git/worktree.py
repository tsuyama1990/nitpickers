import shutil
from pathlib import Path

from src.utils import logger

from .base import BaseGitManager


class GitWorktreeManager(BaseGitManager):
    """Manages ephemeral Git worktrees for parallel execution isolation."""

    def __init__(self, worktree_root: str = "logs/worktrees") -> None:
        super().__init__()
        self.worktree_root = Path(worktree_root)

    async def create_worktree(self, cycle_id: str, branch_name: str) -> Path:
        """Creates a new worktree for a specific cycle and branch."""
        worktree_path = self.worktree_root / f"cycle_{cycle_id}"

        # Cleanup existing if any (shouldn't happen but for robustness)
        if worktree_path.exists():
            await self.remove_worktree(cycle_id)

        self.worktree_root.mkdir(parents=True, exist_ok=True)

        logger.info(f"Creating Git Worktree for cycle {cycle_id} on branch {branch_name}...")
        try:
            # git worktree add -b <temp-branch> <path> <base-branch>
            # This avoids "already used by worktree" errors if branch_name is checked out in /app
            temp_branch = f"isolated-cycle-{cycle_id}-{branch_name}"
            await self._run_git(["worktree", "add", "-b", temp_branch, str(worktree_path), branch_name], check=True)
            logger.info(f"✓ Isolated worktree created at {worktree_path} on branch {temp_branch}")
            return worktree_path.absolute()
        except Exception as e:
            logger.error(f"Failed to create worktree: {e}")
            # Fallback cleanup
            if worktree_path.exists():
                shutil.rmtree(worktree_path, ignore_errors=True)
            raise

    async def remove_worktree(self, cycle_id: str) -> None:
        """Removes a worktree and cleans up the directory."""
        worktree_path = self.worktree_root / f"cycle_{cycle_id}"
        if not worktree_path.exists():
            # Still try to prune if git thinks it exists
            await self._run_git(["worktree", "prune"], check=False)
            return

        logger.info(f"Removing Git Worktree for cycle {cycle_id}...")
        try:
            # We need to find the branch name before removing the worktree
            # Or we can construct it if it follows the pattern isolated-cycle-{cycle_id}-*
            # For robustness, we will attempt to delete the branch we know we created
            # We don't have the original branch_name here, so we might need to query git worktree list
            await self._run_git(["worktree", "remove", str(worktree_path), "--force"], check=False)
            await self._run_git(["worktree", "prune"], check=False)
            
            # Find and delete any branch matching isolated-cycle-{cycle_id}-*
            stdout = await self._run_git(["branch", "--list", f"isolated-cycle-{cycle_id}-*"], check=False)
            if stdout:
                branches = [b.strip().replace("* ", "") for b in stdout.split("\n") if b.strip()]
                for b in branches:
                    await self._run_git(["branch", "-D", b], check=False)
                    logger.info(f"✓ Deleted temporary branch {b}")
        except Exception as e:
            logger.warning(f"Failed to remove worktree gracefully: {e}")

        # Ensure directory is gone
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)
        logger.info(f"✓ Worktree directory {worktree_path} cleaned up.")
