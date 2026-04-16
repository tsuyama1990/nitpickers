from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.services.conflict_manager import ConflictManager, ConflictMarkerRemainsError


@pytest.fixture
def conflict_manager() -> ConflictManager:
    """Create a ConflictManager instance."""
    return ConflictManager()


@pytest.mark.asyncio
async def test_scan_conflicts(conflict_manager: ConflictManager, tmp_path: Path) -> None:
    """Test scan_conflicts extracts git markers correctly."""
    # Create a mock conflicted file
    conflicted_file = tmp_path / "test_file.py"
    conflicted_content = "def my_func():\n<<<<<<< HEAD\n    return 1\n=======\n    return 2\n>>>>>>> feature_branch\n"
    conflicted_file.write_text(conflicted_content)

    # Clean file
    clean_file = tmp_path / "clean_file.py"
    clean_file.write_text("def my_func():\n    return 3\n")

    from src.config import settings

    with (
        patch.object(conflict_manager.runner, "run_command", new_callable=AsyncMock) as mock_run,
        patch.object(settings.paths, "workspace_root", tmp_path),
    ):
        # Mock git status output
        # run_command returns (stdout, stderr, exit_code, timeout_occurred)
        mock_run.return_value = ("UU test_file.py\nM  clean_file.py\n", "", 0, False)

        items = await conflict_manager.scan_conflicts(tmp_path)

        assert len(items) == 1
        item = items[0]
        assert item.file_path == "test_file.py"
        assert len(item.conflict_markers) == 3
        assert item.conflict_markers[0].startswith("<<<<<<<")
        assert item.conflict_markers[1] == "======="
        assert item.conflict_markers[2].startswith(">>>>>>>")


def test_validate_resolution_success(conflict_manager: ConflictManager, tmp_path: Path) -> None:
    """Test validate_resolution on a file without markers."""
    from src.config import settings

    with patch.object(settings.paths, "workspace_root", tmp_path):
        clean_file = tmp_path / "clean_file.py"
        clean_file.write_text("def my_func():\n    return 3\n")

        # Should not raise exception
        assert conflict_manager.validate_resolution(clean_file) is True


def test_validate_resolution_failure(conflict_manager: ConflictManager, tmp_path: Path) -> None:
    """Test validate_resolution on a file with markers."""
    from src.config import settings

    with patch.object(settings.paths, "workspace_root", tmp_path):
        conflicted_file = tmp_path / "conflicted_file.py"
        conflicted_content = "def my_func():\n<<<<<<< HEAD\n    return 1\n=======\n    return 2\n>>>>>>> feature_branch\n"
        conflicted_file.write_text(conflicted_content)

        with pytest.raises(ConflictMarkerRemainsError, match="still contains git conflict markers"):
            conflict_manager.validate_resolution(conflicted_file)


@pytest.mark.asyncio
async def test_scan_conflicts_path_traversal(
    conflict_manager: ConflictManager, tmp_path: Path
) -> None:
    """Test that scan_conflicts blocks path traversal."""
    from src.config import settings

    with patch.object(settings.paths, "workspace_root", tmp_path):
        # Path outside tmp_path
        unsafe_path = tmp_path.parent / "unsafe_path"
        items = await conflict_manager.scan_conflicts(unsafe_path)
        assert items == []

        # Complex path traversal
        traversal_path = tmp_path / ".." / "other_dir"
        items = await conflict_manager.scan_conflicts(traversal_path)
        assert items == []


@pytest.mark.asyncio
async def test_build_conflict_package_path_traversal(
    conflict_manager: ConflictManager, tmp_path: Path
) -> None:
    """Test that build_conflict_package blocks path traversal."""
    from src.config import settings
    from src.domain_models.execution import ConflictRegistryItem

    item = ConflictRegistryItem(file_path="test.py", conflict_markers=[])

    with patch.object(settings.paths, "workspace_root", tmp_path):
        # Path outside tmp_path
        unsafe_path = tmp_path.parent / "unsafe_path"

        with pytest.raises(ValueError, match="escapes workspace root"):
            await conflict_manager.build_conflict_package(item, unsafe_path)


@pytest.mark.asyncio
async def test_build_conflict_package_success(
    conflict_manager: ConflictManager, tmp_path: Path
) -> None:
    from src.config import settings
    from src.domain_models.execution import ConflictRegistryItem

    item = ConflictRegistryItem(file_path="test.py", conflict_markers=[])

    with (
        patch.object(settings.paths, "workspace_root", tmp_path),
        patch.object(conflict_manager.runner, "run_command", new_callable=AsyncMock) as mock_run,
    ):

        def run_command_side_effect(cmd, cwd, check):
            stage = cmd[2].split(":")[1]
            if stage == "1":
                return ("base_content", "", 0, False)
            if stage == "2":
                return ("local_content", "", 0, False)
            if stage == "3":
                return ("remote_content", "", 0, False)
            return ("", "", 1, False)

        mock_run.side_effect = run_command_side_effect

        prompt = await conflict_manager.build_conflict_package(item, tmp_path)

        assert "### Base (元のコード)" in prompt
        assert "base_content" in prompt
        assert "### Branch A の変更 (Local)" in prompt
        assert "local_content" in prompt
        assert "### Branch B の変更 (Remote)" in prompt
        assert "remote_content" in prompt


@pytest.mark.asyncio
async def test_build_conflict_package_no_base(
    conflict_manager: ConflictManager, tmp_path: Path
) -> None:
    import subprocess

    from src.config import settings
    from src.domain_models.execution import ConflictRegistryItem

    item = ConflictRegistryItem(file_path="test.py", conflict_markers=[])

    with (
        patch.object(settings.paths, "workspace_root", tmp_path),
        patch.object(conflict_manager.runner, "run_command", new_callable=AsyncMock) as mock_run,
    ):

        def run_command_side_effect(cmd, cwd, check):
            stage = cmd[2].split(":")[1]
            if stage == "1":
                raise subprocess.CalledProcessError(128, cmd)
            if stage == "2":
                return ("local_content", "", 0, False)
            if stage == "3":
                return ("remote_content", "", 0, False)
            return ("", "", 1, False)

        mock_run.side_effect = run_command_side_effect

        prompt = await conflict_manager.build_conflict_package(item, tmp_path)

        assert "### Base (元のコード)" in prompt
        assert "<FILE_NOT_IN_BASE>" in prompt
        assert "### Branch A の変更 (Local)" in prompt
        assert "local_content" in prompt
        assert "### Branch B の変更 (Remote)" in prompt
        assert "remote_content" in prompt
