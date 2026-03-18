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
    conflicted_content = """def my_func():
<<<<<<< HEAD
    return 1
=======
    return 2
>>>>>>> feature_branch
"""
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
    conflicted_content = """def my_func():
<<<<<<< HEAD
    return 1
=======
    return 2
>>>>>>> feature_branch
"""
    conflicted_file.write_text(conflicted_content)

    with pytest.raises(ConflictMarkerRemainsError, match="still contains git conflict markers"):
        conflict_manager.validate_resolution(conflicted_file)
