import hashlib
import shutil
from pathlib import Path
from unittest.mock import patch

from src.hash_utils import calculate_directory_hash


def test_calculate_directory_hash_empty(tmp_path: Path) -> None:
    """Test with empty files and dirs lists."""
    h1 = calculate_directory_hash(tmp_path, [], [])
    h2 = hashlib.sha256().hexdigest()
    assert h1 == h2


def test_calculate_directory_hash_files(tmp_path: Path) -> None:
    """Test hashing specific files."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("content1")
    file2 = tmp_path / "file2.txt"
    file2.write_text("content2")

    h1 = calculate_directory_hash(tmp_path, ["file1.txt", "file2.txt"], [])
    h2 = calculate_directory_hash(tmp_path, ["file2.txt", "file1.txt"], [])
    assert h1 == h2  # Determinism due to sorted()

    # Change content
    file1.write_text("content1_modified")
    h3 = calculate_directory_hash(tmp_path, ["file1.txt", "file2.txt"], [])
    assert h1 != h3

    # Change filename (via different list)
    h4 = calculate_directory_hash(tmp_path, ["file1.txt"], [])
    h5 = calculate_directory_hash(tmp_path, ["file2.txt"], [])
    assert h4 != h5


def test_calculate_directory_hash_dirs(tmp_path: Path) -> None:
    """Test recursive hashing of directories."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file1 = subdir / "file1.txt"
    file1.write_text("content1")

    subsubdir = subdir / "subsubdir"
    subsubdir.mkdir()
    file2 = subsubdir / "file2.txt"
    file2.write_text("content2")

    h1 = calculate_directory_hash(tmp_path, [], ["subdir"])

    # Verify that changing content in a subdirectory changes the hash
    file2.write_text("content2_modified")
    h2 = calculate_directory_hash(tmp_path, [], ["subdir"])
    assert h1 != h2

    # Verify that adding a new file in a subdirectory changes the hash
    file3 = subsubdir / "file3.txt"
    file3.write_text("content3")
    h3 = calculate_directory_hash(tmp_path, [], ["subdir"])
    assert h2 != h3


def test_calculate_directory_hash_exclusions(tmp_path: Path) -> None:
    """Test that .git and __pycache__ are excluded."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    git_dir = subdir / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("git config")

    pycache_dir = subdir / "__pycache__"
    pycache_dir.mkdir()
    (pycache_dir / "module.pyc").write_bytes(b"bytecode")

    normal_file = subdir / "file.txt"
    normal_file.write_text("content")

    h1 = calculate_directory_hash(tmp_path, [], ["subdir"])

    # Remove git and pycache, hash should stay the same
    shutil.rmtree(git_dir)
    shutil.rmtree(pycache_dir)

    h2 = calculate_directory_hash(tmp_path, [], ["subdir"])
    assert h1 == h2


def test_calculate_directory_hash_non_existent(tmp_path: Path) -> None:
    """Test that non-existent files and dirs don't cause errors."""
    h = calculate_directory_hash(tmp_path, ["non_existent.txt"], ["non_existent_dir"])
    assert h == hashlib.sha256().hexdigest()


def test_calculate_directory_hash_read_error(tmp_path: Path) -> None:
    """Test that read errors are handled gracefully."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("content1")

    # Mock read_bytes to raise an exception
    with patch.object(Path, "read_bytes", side_effect=Exception("Read error")):
        # It should continue without crashing
        h = calculate_directory_hash(tmp_path, ["file1.txt"], [])
        # Since it failed to read content, it only updated with the filename (absolute path in this case)
        hasher = hashlib.sha256()
        hasher.update(str(file1).encode())
        assert h == hasher.hexdigest()


def test_calculate_directory_hash_dir_read_error(tmp_path: Path) -> None:
    """Test that read errors during directory traversal are handled gracefully."""
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file1 = subdir / "file1.txt"
    file1.write_text("content1")

    # Use a mock that only fails for file1.txt to be more precise
    original_read_bytes = Path.read_bytes

    def mocked_read_bytes(self: Path) -> bytes:
        if self.name == "file1.txt":
            raise Exception("Read error")
        return original_read_bytes(self)

    with patch.object(Path, "read_bytes", autospec=True, side_effect=mocked_read_bytes):
        h = calculate_directory_hash(tmp_path, [], ["subdir"])
        # Should only have hashed the relative filename
        hasher = hashlib.sha256()
        hasher.update(str(file1.relative_to(tmp_path)).encode())
        assert h == hasher.hexdigest()
