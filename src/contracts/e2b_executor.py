import abc

from src.domain_models.execution import E2BExecutionResult


class E2BExecutorService(abc.ABC):
    """
    Interface for executing tests and code in an isolated E2B sandbox environment.
    """

    @abc.abstractmethod
    async def push_files(self, local_path: str, remote_path: str) -> None:
        """Push files from local path to remote sandbox path."""

    @abc.abstractmethod
    async def run_tests(self, command: str) -> E2BExecutionResult:
        """Run tests via the given command and return execution artifacts."""

    @abc.abstractmethod
    async def cleanup(self) -> None:
        """Clean up resources associated with the sandbox."""
