from .git.base import BaseGitManager
from .git.branching import GitBranchingMixin
from .git.checkout import GitCheckoutMixin
from .git.merging import GitMergingMixin
from .git.state import GitStateMixin


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

    def read_file_from_branch(self, branch: str, filepath: str) -> str:
        """Reads a file from a specific branch using git show."""
        result = self._run_git(["show", f"{branch}:{filepath}"])
        if result is None:
            msg = f"Could not read {filepath} from branch {branch}"
            raise RuntimeError(msg)
        return str(result)
