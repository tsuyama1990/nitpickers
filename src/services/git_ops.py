import asyncio
from pathlib import Path

from .git.base import BaseGitManager
from .git.branching import GitBranchingMixin
from .git.checkout import GitCheckoutMixin
from .git.merging import GitMergingMixin
from .git.state import GitStateMixin

# Global lock to synchronize parallel access to the local Git repository
workspace_lock = asyncio.Lock()

# Global state to track last pushed commit hashes per branch to avoid redundant pushes in parallel batches
_pushed_commit_hashes: dict[str, str] = {}


class GitManager(
    GitBranchingMixin, GitCheckoutMixin, GitMergingMixin, GitStateMixin, BaseGitManager
):
    """
    Manages Git operations for the AC-CDD workflow.
    Refactored to composite mixins for better maintainability.
    """

    # Re-expose constant for compatibility if anything imports it directly
    STATE_BRANCH = "ac-cdd/state"

    def __init__(self, cwd: Path | None = None) -> None:
        super().__init__(cwd=cwd)
