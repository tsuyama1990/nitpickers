from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.domain_models.execution import ConflictRegistryItem
from src.services.conflict_manager import ConflictManager


@pytest.fixture
def conflict_manager() -> ConflictManager:
    """Create a ConflictManager instance."""
    return ConflictManager()


@pytest.mark.asyncio
async def test_build_conflict_package_missing_base(
    conflict_manager: ConflictManager, tmp_path: Path
) -> None:
    """Test that build_conflict_package correctly handles a file newly created in Branch A, missing in Base."""

    item = ConflictRegistryItem(
        file_path="new_file.py",
        conflict_markers=["<<<<<<< HEAD", "=======", ">>>>>>> branch"],
    )

    from src.config import settings

    with (
        patch.object(conflict_manager.runner, "run_command", new_callable=AsyncMock) as mock_run,
        patch.object(settings.paths, "workspace_root", tmp_path),
    ):
        # We mock git show outputs
        # Stage 1 (Base): Missing (fails)
        # Stage 2 (Local): "local_code"
        # Stage 3 (Remote): "remote_code"
        def mock_git_show(cmd: list[str], cwd: Path, check: bool) -> tuple[str, str, int, bool]:
            if cmd == ["git", "show", ":1:new_file.py"]:
                msg = "fatal: Path 'new_file.py' does not exist in 'HEAD'"
                raise RuntimeError(msg)
            if cmd == ["git", "show", ":2:new_file.py"]:
                return ("local_code", "", 0, False)
            if cmd == ["git", "show", ":3:new_file.py"]:
                return ("remote_code", "", 0, False)
            return ("", "", 0, False)

        mock_run.side_effect = mock_git_show

        prompt = await conflict_manager.build_conflict_package(item, tmp_path)

        # Verify the prompt string formatting and the specific injection marker
        assert "<FILE_NOT_IN_BASE>" in prompt
        assert "### Base (元のコード)\n```python\n<FILE_NOT_IN_BASE>\n```" in prompt
        assert "### Branch A の変更 (Local)\n```python\nlocal_code\n```" in prompt
        assert "### Branch B の変更 (Remote)\n```python\nremote_code\n```" in prompt


@pytest.mark.asyncio
async def test_build_conflict_package_success(
    conflict_manager: ConflictManager, tmp_path: Path
) -> None:
    """Test standard 3-way diff extraction."""

    item = ConflictRegistryItem(
        file_path="existing_file.py",
        conflict_markers=["<<<<<<< HEAD", "=======", ">>>>>>> branch"],
    )

    from src.config import settings

    with (
        patch.object(conflict_manager.runner, "run_command", new_callable=AsyncMock) as mock_run,
        patch.object(settings.paths, "workspace_root", tmp_path),
    ):

        def mock_git_show(cmd: list[str], cwd: Path, check: bool) -> tuple[str, str, int, bool]:
            if cmd == ["git", "show", ":1:existing_file.py"]:
                return ("base_code", "", 0, False)
            if cmd == ["git", "show", ":2:existing_file.py"]:
                return ("local_code", "", 0, False)
            if cmd == ["git", "show", ":3:existing_file.py"]:
                return ("remote_code", "", 0, False)
            return ("", "", 0, False)

        mock_run.side_effect = mock_git_show

        prompt = await conflict_manager.build_conflict_package(item, tmp_path)

        assert "### Base (元のコード)\n```python\nbase_code\n```" in prompt
        assert "### Branch A の変更 (Local)\n```python\nlocal_code\n```" in prompt
        assert "### Branch B の変更 (Remote)\n```python\nremote_code\n```" in prompt
