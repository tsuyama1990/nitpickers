# A thin stub that provides basic local Git wrappers replacing the old GitManager
# to prevent breaking test dependencies and nodes needing basic git operations
# that don't involve GitHub writes or state management.

from src.process_runner import ProcessRunner


class GitManager:
    def __init__(self) -> None:
        self.runner = ProcessRunner()

    async def get_changed_files(self, base_branch: str = "main") -> list[str]:
        stdout, _, code, _ = await self.runner.run_command(
            ["git", "diff", "--name-only", f"{base_branch}...HEAD"]
        )
        if code != 0:
            return []
        return [f.strip() for f in stdout.split("\n") if f.strip()]

    async def get_current_branch(self) -> str:
        stdout, _, _, _ = await self.runner.run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"]
        )
        return stdout.strip()

    async def checkout_branch(self, branch: str) -> None:
        await self.runner.run_command(["git", "checkout", branch])

    async def get_pr_base_branch(self, pr_url: str) -> str | None:
        # Stub
        return "main"

    async def get_current_commit(self) -> str:
        stdout, _, _, _ = await self.runner.run_command(["git", "rev-parse", "HEAD"])
        return stdout.strip()

    async def get_remote_url(self) -> str | None:
        stdout, _, code, _ = await self.runner.run_command(
            ["git", "remote", "get-url", "origin"], check=False
        )
        return stdout.strip() if code == 0 else None
