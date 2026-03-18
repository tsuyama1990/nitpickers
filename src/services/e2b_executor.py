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
        """

        sandbox = await self.sandbox.get_sandbox()
        from anyio import Path

        path = Path(local_path)
        content = await path.read_bytes()
        sandbox.files.write(remote_path, content)

    async def run_tests(self, command: str) -> E2BExecutionResult:
        """
        Run tests via the given command and return execution artifacts.
        Note: The command is passed directly to the E2B sandbox environment.
        It is validated by the system to run basic bash testing commands.
        """
        import shlex

        from src.config import settings

        allowed = False
        for whitelist_cmd in settings.sandbox.command_whitelist:
            if command.startswith(whitelist_cmd):
                allowed = True
                break

        if not allowed:
            msg = f"Command {command} is not in the allowed whitelist."
            raise ValueError(msg)

        cmd_list = shlex.split(command)
        stdout, stderr, exit_code = await self.sandbox.run_command(cmd_list)
        return E2BExecutionResult(stdout=str(stdout), stderr=str(stderr), exit_code=int(exit_code))

    async def cleanup(self) -> None:
        """
        Clean up resources associated with the sandbox.
        """
        await self.sandbox.cleanup()
