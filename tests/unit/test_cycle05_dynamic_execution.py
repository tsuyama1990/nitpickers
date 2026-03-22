from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.services.git_ops import GitManager

from src.enums import FlowStatus, WorkPhase
from src.services.uat_usecase import UatUseCase
from src.state import CycleState


@pytest.fixture
def mock_git_manager() -> MagicMock:
    git_mgr = MagicMock(spec=GitManager)
    git_mgr.merge_pr = AsyncMock()
    return git_mgr


@pytest.mark.asyncio
@patch("src.services.uat_usecase.ProcessRunner")
@patch("src.services.uat_usecase.settings")
async def test_uat_usecase_dynamic_execution_success(
    mock_settings: MagicMock, mock_process_runner_cls: MagicMock, mock_git_manager: MagicMock
) -> None:
    # Setup
    mock_process_runner = MagicMock()
    mock_process_runner.run_command = AsyncMock(return_value=("pytest success", "", 0, False))
    mock_process_runner_cls.return_value = mock_process_runner
    mock_settings.uat.test_cmd = "uv run pytest tests/uat/"
    mock_settings.uat.db_reset_cmd = None

    state = CycleState(
        cycle_id="01", current_phase=WorkPhase.CODER
    )
    state.pr_url = "https://github.com/owner/repo/pull/1"

    use_case = UatUseCase(mock_git_manager)

    # Act
    result = await use_case.execute(state)

    # Assert
    mock_process_runner.run_command.assert_awaited_once()
    assert result["status"] == FlowStatus.COMPLETED
    mock_git_manager.merge_pr.assert_awaited_once_with("1")


@pytest.mark.asyncio
@patch("src.services.uat_usecase.ProcessRunner")
@patch("src.services.uat_usecase.settings")
@patch("pathlib.Path.glob")
async def test_uat_usecase_dynamic_execution_failure(
    mock_glob: MagicMock,
    mock_settings: MagicMock,
    mock_process_runner_cls: MagicMock,
    mock_git_manager: MagicMock,
    tmp_path: Path,
) -> None:
    # Setup
    mock_process_runner = MagicMock()
    mock_process_runner.run_command = AsyncMock(
        return_value=("pytest fail", "error trace", 1, False)
    )
    mock_process_runner_cls.return_value = mock_process_runner
    mock_settings.uat.test_cmd = "uv run pytest tests/uat/"
    mock_settings.uat.db_reset_cmd = None

    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()

    # Mock files
    png_file = artifacts_dir / "test_login.png"
    zip_file = artifacts_dir / "test_login_trace.zip"

    png_file.write_bytes(b"dummy")
    zip_file.write_bytes(b"dummy")

    # Return actual Path objects so iterdir/glob work properly if used
    mock_glob.return_value = [png_file]

    # Use actual Path mock directly to bypass the new rigorous checks in uat_usecase.py
    mock_dir = MagicMock(spec=Path)
    mock_dir.exists.return_value = True
    mock_dir.is_symlink.return_value = False
    mock_dir.is_dir.return_value = True

    mock_resolved = MagicMock(spec=Path)
    mock_resolved.is_relative_to.return_value = True
    mock_resolved.glob.return_value = [png_file]
    mock_resolved.__truediv__.side_effect = artifacts_dir.__truediv__
    mock_dir.resolve.return_value = mock_resolved

    mock_settings.paths.artifacts_dir = mock_dir

    state = CycleState(cycle_id="01", current_phase=WorkPhase.CODER)

    use_case = UatUseCase(mock_git_manager)

    # Act
    result = await use_case.execute(state)

    # Assert
    mock_process_runner.run_command.assert_awaited_once()
    assert result["status"] == FlowStatus.UAT_FAILED

    uat_state = result["uat_execution_state"]
    assert uat_state is not None
    assert uat_state.exit_code == 1
    assert uat_state.stdout == "pytest fail"
    assert uat_state.stderr == "error trace"

    assert len(uat_state.artifacts) == 1
    artifact = uat_state.artifacts[0]
    assert artifact.test_id == "test_login"
    assert artifact.screenshot_path == str(png_file)
    assert artifact.trace_path == str(zip_file)
    assert artifact.traceback == "error trace"[-mock_settings.uat.traceback_limit :]
