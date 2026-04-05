import asyncio

from .git.base import BaseGitManager
from .git.branching import GitBranchingMixin
from .git.checkout import GitCheckoutMixin
from .git.merging import GitMergingMixin
from .git.state import GitStateMixin


# Global lock to synchronize parallel access to the local Git repository
workspace_lock = asyncio.Lock()


class GitManager(
    GitBranchingMixin, GitCheckoutMixin, GitMergingMixin, GitStateMixin, BaseGitManager
):
    """
    Manages Git operations for the AC-CDD workflow.
    Refactored to composite mixins for better maintainability.
    """

    # Re-expose constant for compatibility if anything imports it directly
    STATE_BRANCH = "ac-cdd/state"

    def __init__(self) -> None:
        super().__init__()
