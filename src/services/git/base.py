from pathlib import Path

from src.config import settings
from src.process_runner import ProcessRunner
from src.utils import logger


class BaseGitManager:
    """Base class for Git operations."""

    def __init__(self) -> None:
        self.runner = ProcessRunner()
        self.git_cmd = "git"
        self.gh_cmd = settings.tools.gh_cmd

    async def _ensure_no_lock(self) -> None:
        """Removes stale index.lock file if it exists."""
        lock_file = Path.cwd() / ".git" / "index.lock"
        if lock_file.exists():
            try:
                # We assume single-threaded git access in this agent context.
                lock_file.unlink()
                logger.warning("Removed stale .git/index.lock file")
            except OSError as e:
                logger.warning(f"Could not remove .git/index.lock: {e}")

    async def _run_git(self, args: list[str], check: bool = True) -> str:
        # Check for lock before running any command
        import asyncio
        import logging
        import random
        logger = logging.getLogger(__name__)
        for attempt in range(5):
            await self._ensure_no_lock()
            cmd = [self.git_cmd, *args]
            stdout, stderr, code, _ = await self.runner.run_command(cmd, check=False)

            error_msg = str(stderr).strip() or str(stdout).strip()

            if code == 0:
                return str(stdout).strip()

            if "index.lock" in error_msg and attempt < 4:
                logger.warning(f"Index locked, retrying {args}...")
                await asyncio.sleep(random.uniform(  # noqa: S311
                    0.5, 2.0))
                continue

            if args and args[0] == "pull" and ("no tracking information" in error_msg or "could not read Username" in error_msg):
                logger.warning(f"Git pull tracking/auth error suppressed: {error_msg}")
                return ""

            if code != 0 and check:
                msg = f"Git command failed: {' '.join(cmd)} - Stderr: {error_msg}"
                raise RuntimeError(msg)
            return str(stdout).strip()
        return ""


    async def get_current_commit(self) -> str:
        """Returns the current commit hash (HEAD)."""
        stdout, _stderr, _code, _ = await self.runner.run_command(
            [self.git_cmd, "rev-parse", "HEAD"], check=True
        )
        return str(stdout).strip()

    async def get_status(self) -> str:
        return await self._run_git(["status", "--porcelain"], check=False)

    async def add_all(self) -> None:
        await self._run_git(["add", "."])

    async def commit(self, message: str) -> None:
        await self._run_git(["commit", "-m", message])

    async def reset_hard(self) -> None:
        await self._run_git(["reset", "--hard", "HEAD"])
        await self._run_git(["clean", "-fd"])
