from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.git.checkout import GitCheckoutMixin


class TestGitCheckout:
    """Tests for GitCheckoutMixin."""

    @pytest.mark.asyncio
    async def test_pull_changes_uses_rebase(self) -> None:
        """Verifies that pull_changes uses --rebase."""

        # Create a concrete class mixing in GitCheckoutMixin
        class MockGit(GitCheckoutMixin):
            def __init__(self) -> None:
                self.runner = MagicMock()
                self.git_cmd = "git"
                self._run_git = AsyncMock()  # type: ignore[method-assign]

        git = MockGit()

        await git.pull_changes()

        # Verify _run_git was called with ["pull", "--rebase"]
        git._run_git.assert_called_with(["pull", "--rebase"])  # type: ignore[attr-defined]
