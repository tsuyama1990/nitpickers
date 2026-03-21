from pathlib import Path

from src.process_runner import ProcessRunner
from src.utils import logger


class DependencyManager:
    """Manages project dependencies and git initialization."""

    def __init__(self) -> None:
        self.runner = ProcessRunner()


    async def initialize_dependencies_and_git(self) -> None:
        if not (Path.cwd() / "pyproject.toml").exists():
            logger.info("Initializing pyproject.toml...")
            await self.runner.run_command(["uv", "init", "--no-workspace"], check=False)

        logger.info("Adding development dependencies (ruff, mypy, pytest)...")
        try:
            await self.runner.run_command(
                ["uv", "add", "--dev", "--no-sync", "ruff", "mypy", "pytest", "pytest-cov"],
                check=True,
            )
            logger.info("✓ Dependencies added to pyproject.toml successfully.")
        except Exception as e:
            logger.warning(f"Failed to install dependencies: {e}")

        if not (Path.cwd() / ".git").exists():
            logger.info("Initializing Git repository...")
            await self.runner.run_command(["git", "init"], check=True)

        try:
            await self.runner.run_command(["git", "add", "."], check=True)
            await self.runner.run_command(["git", "commit", "-m", "Initialize project with AC-CDD structure and dev dependencies"], check=False)
            logger.info("✓ Changes committed.")
        except Exception as e:
            logger.warning(f"Git operations failed: {e}")

    async def sync_dependencies(self) -> None:
        """Syncs dependencies using uv."""
        logger.info("[ProjectManager] Syncing dependencies...")
        try:
            await self.runner.run_command(["uv", "sync", "--dev"], check=True)

            _stdout, _stderr, code_ruff, _ = await self.runner.run_command(
                ["uv", "run", "ruff", "--version"], check=False
            )
            _stdout, _stderr, code_mypy, _ = await self.runner.run_command(
                ["uv", "run", "mypy", "--version"], check=False
            )

            if code_ruff != 0 or code_mypy != 0:
                logger.info("[ProjectManager] Installing missing linters...")
                await self.runner.run_command(["uv", "add", "--dev", "ruff", "mypy"], check=True)

            logger.info("[ProjectManager] Environment prepared.")
        except Exception as e:
            logger.warning(f"[ProjectManager] Dependency sync failed: {e}")
