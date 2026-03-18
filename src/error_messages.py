"""Error message helpers for AC-CDD."""


class RecoveryMessages:
    """Helper class for formatting recovery error messages."""

    @staticmethod
    def branch_not_found(branch_name: str, session_file: str) -> str:
        """Message for when a local integration branch is missing."""
        return (
            f"Integration branch '{branch_name}' not found locally.\n"
            f"Please check your session file ({session_file}) or try to reconcile."
        )

    @staticmethod
    def remote_branch_missing(branch_name: str) -> str:
        """Message for when a remote integration branch is missing."""
        return (
            f"Integration branch '{branch_name}' does not exist on remote 'origin'.\n"
            "You may need to push it or create a new session."
        )
