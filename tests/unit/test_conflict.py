from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.conflict_manager import ConflictManager, ConflictMarkerRemainsError


@pytest.fixture
def conflict_manager() -> ConflictManager:
    """Create a ConflictManager instance."""
    return ConflictManager()


def test_scan_conflicts(conflict_manager: ConflictManager, tmp_path: Path) -> None:
    """Test scan_conflicts extracts git markers correctly."""
    # Create a mock conflicted file
    conflicted_file = tmp_path / "test_file.py"
    lines = [
        "def my_func():",
        "<<<<<<< HEAD",
        "    return 1",
        "=======",
        "    return 2",
        ">>>>>>> feature_branch",
        "",
    ]
    conflicted_content = "\n".join(lines)
    conflicted_file.write_text(conflicted_content)

    # Clean file
    clean_file = tmp_path / "clean_file.py"
    clean_file.write_text("def my_func():\n    return 3\n")

    with patch("subprocess.run") as mock_run:
        # Mock git status output
        mock_run.return_value.stdout = "UU test_file.py\nM  clean_file.py\n"

        items = conflict_manager.scan_conflicts(tmp_path)

        assert len(items) == 1
        item = items[0]
        assert item.file_path == "test_file.py"
        assert len(item.conflict_markers) == 3
        assert item.conflict_markers[0].startswith("<<<<<<<")
        assert item.conflict_markers[1] == "======="
        assert item.conflict_markers[2].startswith(">>>>>>>")


def test_validate_resolution_success(conflict_manager: ConflictManager, tmp_path: Path) -> None:
    """Test validate_resolution on a file without markers."""
    clean_file = tmp_path / "clean_file.py"
    clean_file.write_text("def my_func():\n    return 3\n")

    # Should not raise exception
    assert conflict_manager.validate_resolution(clean_file) is True


def test_validate_resolution_failure(conflict_manager: ConflictManager, tmp_path: Path) -> None:
    """Test validate_resolution on a file with markers."""
    conflicted_file = tmp_path / "conflicted_file.py"
    lines = [
        "def my_func():",
        "<<<<<<< HEAD",
        "    return 1",
        "=======",
        "    return 2",
        ">>>>>>> feature_branch",
        "",
    ]
    conflicted_content = "\n".join(lines)
    conflicted_file.write_text(conflicted_content)

    with pytest.raises(ConflictMarkerRemainsError, match="still contains git conflict markers"):
        conflict_manager.validate_resolution(conflicted_file)


@pytest.mark.asyncio
async def test_build_conflict_package_all_exist(
    conflict_manager: ConflictManager, tmp_path: Path
) -> None:
    from src.domain_models.execution import ConflictRegistryItem

    item = ConflictRegistryItem(
        file_path="test_file.py", conflict_markers=["<<<<<<<", "=======", ">>>>>>>"]
    )

    with patch("src.process_runner.ProcessRunner.run_command") as mock_run:
        # Mocking ProcessRunner to return code for base, local, remote respectively
        mock_run.side_effect = [
            ("def base():\n    pass", "", 0, False),
            ("def local():\n    pass", "", 0, False),
            ("def remote():\n    pass", "", 0, False),
        ]

        prompt = await conflict_manager.build_conflict_package(item, tmp_path)

        assert "Base" in prompt
        assert "def base():\n    pass" in prompt
        assert "Local" in prompt
        assert "def local():\n    pass" in prompt
        assert "Remote" in prompt
        assert "def remote():\n    pass" in prompt


@pytest.mark.asyncio
async def test_build_conflict_package_no_base(
    conflict_manager: ConflictManager, tmp_path: Path
) -> None:
    from src.domain_models.execution import ConflictRegistryItem

    item = ConflictRegistryItem(
        file_path="new_file.py", conflict_markers=["<<<<<<<", "=======", ">>>>>>>"]
    )

    with patch("src.process_runner.ProcessRunner.run_command") as mock_run:
        # Mocking ProcessRunner to return code, base fails (new file)
        mock_run.side_effect = [
            ("", "fatal: path 'new_file.py' does not exist in 'HEAD'", 128, False),
            ("def local():\n    pass", "", 0, False),
            ("def remote():\n    pass", "", 0, False),
        ]

        prompt = await conflict_manager.build_conflict_package(item, tmp_path)

        assert "<FILE_NOT_IN_BASE>" in prompt
        assert "Local" in prompt
        assert "Remote" in prompt
