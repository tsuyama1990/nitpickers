from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.domain_models.execution import E2BExecutionResult
from src.services.e2b_executor import E2BExecutorServiceImpl


@pytest.fixture()
def mock_sandbox_runner() -> Generator[Any, None, None]:
    with patch("src.sandbox.SandboxRunner", autospec=True) as mock_cls:
        mock_instance = mock_cls.return_value
        mock_instance.run_command = AsyncMock()
        mock_instance.cleanup = AsyncMock()
        mock_instance.get_sandbox = AsyncMock()
        mock_sandbox = AsyncMock()
        mock_sandbox.files.write = AsyncMock()
        mock_instance.get_sandbox.return_value = mock_sandbox
        yield mock_instance


@pytest.mark.asyncio()
async def test_run_tests_success(mock_sandbox_runner: Any) -> None:
    # Setup mock
    mock_sandbox_runner.run_command.return_value = ("Tests passed!", "", 0)

    executor = E2BExecutorServiceImpl(sandbox_runner=mock_sandbox_runner)
    result = await executor.run_tests("pytest tests/")

    assert isinstance(result, E2BExecutionResult)
    assert result.exit_code == 0
    assert result.stdout == "Tests passed!"
    assert result.stderr == ""


@pytest.mark.asyncio()
async def test_run_tests_failure(mock_sandbox_runner: Any) -> None:
    # Setup mock
    mock_sandbox_runner.run_command.return_value = ("Running tests...", "AssertionError: Failed", 1)

    executor = E2BExecutorServiceImpl(sandbox_runner=mock_sandbox_runner)
    result = await executor.run_tests("pytest tests/")

    assert isinstance(result, E2BExecutionResult)
    assert result.exit_code == 1
    assert result.stdout == "Running tests..."
    assert result.stderr == "AssertionError: Failed"


@pytest.mark.asyncio()
async def test_push_files(mock_sandbox_runner: Any) -> None:
    # Setup mock
    mock_sandbox_runner._sync_to_sandbox = AsyncMock()

    executor = E2BExecutorServiceImpl(sandbox_runner=mock_sandbox_runner)

    with patch("anyio.Path.read_bytes", new_callable=AsyncMock) as mock_read:
        mock_read.return_value = b"test_data"
        await executor.push_files("local/path", "remote/path")


@pytest.mark.asyncio()
async def test_cleanup(mock_sandbox_runner: Any) -> None:
    executor = E2BExecutorServiceImpl(sandbox_runner=mock_sandbox_runner)
    await executor.cleanup()
    mock_sandbox_runner.cleanup.assert_awaited_once()
