from src.contracts.e2b_executor import E2BExecutorService
from src.domain_models.execution import E2BExecutionResult
from src.sandbox import SandboxRunner


class E2BExecutorServiceImpl(E2BExecutorService):
    """
    Implementation of the E2BExecutorService using the SandboxRunner.
    """

    def __init__(self, sandbox_runner: SandboxRunner | None = None) -> None:
        self.sandbox = sandbox_runner or SandboxRunner()

    async def push_files(self, local_path: str, remote_path: str) -> None:
        """
        Push files from local path to remote sandbox path.
        Note: SandboxRunner._sync_to_sandbox handles syncing automatically.
        """
        # We explicitly trigger a sync if needed, though run_command also syncs.
        sandbox = await self.sandbox._get_sandbox()
        await self.sandbox._sync_to_sandbox(sandbox)

    async def run_tests(self, command: str) -> E2BExecutionResult:
        """
        Run tests via the given command and return execution artifacts.
        """
        import shlex

        cmd_list = shlex.split(command)
        stdout, stderr, exit_code = await self.sandbox.run_command(cmd_list)
        return E2BExecutionResult(stdout=stdout, stderr=stderr, exit_code=exit_code)

    async def cleanup(self) -> None:
        """
        Clean up resources associated with the sandbox.
        """
        await self.sandbox.cleanup()
