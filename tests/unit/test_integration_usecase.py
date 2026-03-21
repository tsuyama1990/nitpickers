from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.domain_models.execution import ConflictRegistryItem
from src.services.integration_usecase import IntegrationUsecase, MaxRetriesExceededError
from src.services.jules_client import JulesClient
from src.state import IntegrationState


@pytest.fixture
def repo_path(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def mock_jules() -> MagicMock:
    jules = MagicMock(spec=JulesClient)
    # It's a synchronous method now
    jules.create_master_integrator_session.return_value = "test-session-id"
    return jules


@pytest.mark.asyncio
async def test_integration_usecase_success(repo_path: Path, mock_jules: MagicMock) -> None:
    # Setup conflict file
    file_path = "fileA.py"
    full_path = repo_path / file_path
    full_path.write_text("<<<<<<< HEAD\ncodeA\n=======\ncodeB\n>>>>>>> branch", encoding="utf-8")

    item = ConflictRegistryItem(
        file_path=file_path,
        conflict_markers=["<<<<<<< HEAD", "=======", ">>>>>>> branch"],
        resolution_attempts=0,
        resolved=False,
    )
    state = IntegrationState(unresolved_conflicts=[item])

    usecase = IntegrationUsecase(github_write_tools=[])

    # Mock LLM returning clean code on first try
    mock_jules.send_message_to_session.return_value = "```python\nclean_code\n```"

    new_state = await usecase.run_integration_loop(state, repo_path)

    assert new_state.master_integrator_session_id == "test-session-id"
    assert new_state.unresolved_conflicts[0].resolved is True
    assert new_state.unresolved_conflicts[0].resolution_attempts == 1
    assert full_path.read_text() == "clean_code"


@pytest.mark.asyncio
async def test_integration_usecase_retry_loop(repo_path: Path, mock_jules: MagicMock) -> None:
    # Setup conflict file
    file_path = "fileA.py"
    full_path = repo_path / file_path
    full_path.write_text("<<<<<<< HEAD\ncodeA\n=======\ncodeB\n>>>>>>> branch", encoding="utf-8")

    item = ConflictRegistryItem(
        file_path=file_path,
        conflict_markers=["<<<<<<< HEAD", "=======", ">>>>>>> branch"],
        resolution_attempts=0,
        resolved=False,
    )
    state = IntegrationState(unresolved_conflicts=[item])

    usecase = IntegrationUsecase(github_write_tools=[])

    # Mock LLM returning bad code on first try, clean code on second
    mock_jules.send_message_to_session.side_effect = [
        "```python\n<<<<<<< HEAD\nbad\n=======\n```",
        "```python\nclean_code\n```",
    ]

    new_state = await usecase.run_integration_loop(state, repo_path)

    assert new_state.unresolved_conflicts[0].resolved is True
    assert new_state.unresolved_conflicts[0].resolution_attempts == 2
    assert mock_jules.send_message_to_session.call_count == 2
    assert full_path.read_text() == "clean_code"


@pytest.mark.asyncio
async def test_integration_usecase_max_retries_exceeded(
    repo_path: Path, mock_jules: MagicMock
) -> None:
    # Setup conflict file
    file_path = "fileA.py"
    full_path = repo_path / file_path
    full_path.write_text("<<<<<<< HEAD\ncodeA\n=======\ncodeB\n>>>>>>> branch", encoding="utf-8")

    item = ConflictRegistryItem(
        file_path=file_path,
        conflict_markers=["<<<<<<< HEAD", "=======", ">>>>>>> branch"],
        resolution_attempts=0,
        resolved=False,
    )
    state = IntegrationState(unresolved_conflicts=[item])

    usecase = IntegrationUsecase(github_write_tools=[])

    # Mock LLM constantly returning bad code
    mock_jules.send_message_to_session.return_value = "```python\n<<<<<<< HEAD\nbad\n=======\n```"

    with pytest.raises(MaxRetriesExceededError):
        await usecase.run_integration_loop(state, repo_path)

    assert state.unresolved_conflicts[0].resolved is False
    assert state.unresolved_conflicts[0].resolution_attempts == 3
    assert mock_jules.send_message_to_session.call_count == 3
