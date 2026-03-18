from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from src.domain_models.execution import ConflictRegistryItem
from src.services.integration_usecase import IntegrationUsecase, MaxRetriesExceededError
from src.state import IntegrationState


# Scenario ID 07-01: Successful Stateful Conflict Resolution
@pytest.mark.asyncio
async def test_uat_07_01_successful_stateful_conflict_resolution(tmp_path: Path):
    file_a = tmp_path / "fileA.py"
    file_b = tmp_path / "fileB.py"

    file_a.write_text("<<<<<<< HEAD\ncodeA\n=======\ncodeB\n>>>>>>> branch")
    file_b.write_text("<<<<<<< HEAD\ncodeC\n=======\ncodeD\n>>>>>>> branch")

    items = [
        ConflictRegistryItem(file_path="fileA.py", conflict_markers=["<<<<<<< HEAD"], resolution_attempts=0, resolved=False),
        ConflictRegistryItem(file_path="fileB.py", conflict_markers=["<<<<<<< HEAD"], resolution_attempts=0, resolved=False)
    ]
    state = IntegrationState(unresolved_conflicts=items)

    from unittest.mock import MagicMock
    mock_jules = AsyncMock()
    mock_jules.create_master_integrator_session = MagicMock(return_value="master-session-001")
    # Resolve files in sequence
    mock_jules.send_message_to_session.side_effect = ["```python\nfixedA\n```", "```python\nfixedB\n```"]

    usecase = IntegrationUsecase(jules_client=mock_jules)

    new_state = await usecase.run_integration_loop(state, tmp_path)

    assert new_state.master_integrator_session_id == "master-session-001"
    assert new_state.unresolved_conflicts[0].resolved is True
    assert new_state.unresolved_conflicts[1].resolved is True
    assert mock_jules.send_message_to_session.call_count == 2
    assert file_a.read_text() == "fixedA"
    assert file_b.read_text() == "fixedB"

# Scenario ID 07-02: Conflict Marker Retry Loop
@pytest.mark.asyncio
async def test_uat_07_02_conflict_marker_retry_loop(tmp_path: Path):
    file_a = tmp_path / "fileA.py"
    file_a.write_text("<<<<<<< HEAD\ncodeA\n=======\ncodeB\n>>>>>>> branch")

    item = ConflictRegistryItem(file_path="fileA.py", conflict_markers=["<<<<<<< HEAD"], resolution_attempts=0, resolved=False)
    state = IntegrationState(unresolved_conflicts=[item])

    from unittest.mock import MagicMock
    mock_jules = AsyncMock()
    mock_jules.create_master_integrator_session = MagicMock(return_value="master-session-002")
    # Fails first, succeeds second
    mock_jules.send_message_to_session.side_effect = [
        "```python\n<<<<<<< HEAD\nbad code\n=======\n```",
        "```python\ngood code\n```"
    ]

    usecase = IntegrationUsecase(jules_client=mock_jules)
    new_state = await usecase.run_integration_loop(state, tmp_path)

    assert new_state.unresolved_conflicts[0].resolved is True
    assert new_state.unresolved_conflicts[0].resolution_attempts == 2
    assert mock_jules.send_message_to_session.call_count == 2

    # Assert second prompt contained failure feedback
    second_call_prompt = mock_jules.send_message_to_session.call_args_list[1][0][1]
    assert "Your resolution failed. Conflict markers `<<<<<<<` still exist." in second_call_prompt

# Scenario ID 07-03: Maximum Conflict Retries Exceeded
@pytest.mark.asyncio
async def test_uat_07_03_maximum_conflict_retries_exceeded(tmp_path: Path):
    file_a = tmp_path / "fileA.py"
    file_a.write_text("<<<<<<< HEAD\ncodeA\n=======\ncodeB\n>>>>>>> branch")

    item = ConflictRegistryItem(file_path="fileA.py", conflict_markers=["<<<<<<< HEAD"], resolution_attempts=0, resolved=False)
    state = IntegrationState(unresolved_conflicts=[item])

    from unittest.mock import MagicMock
    mock_jules = AsyncMock()
    mock_jules.create_master_integrator_session = MagicMock(return_value="master-session-003")
    # Never succeeds
    mock_jules.send_message_to_session.return_value = "```python\n<<<<<<< HEAD\nbad code\n=======\n```"

    usecase = IntegrationUsecase(jules_client=mock_jules)

    with pytest.raises(MaxRetriesExceededError):
        await usecase.run_integration_loop(state, tmp_path)

    assert state.unresolved_conflicts[0].resolved is False
    assert state.unresolved_conflicts[0].resolution_attempts == 3
