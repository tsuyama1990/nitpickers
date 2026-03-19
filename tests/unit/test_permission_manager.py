import sys
from unittest.mock import MagicMock

class MockModule(MagicMock):
    def __getattr__(self, name):
        return MagicMock()

# Mock only necessary parts if possible, but the app seems tightly coupled
sys.modules["dotenv"] = MockModule()
sys.modules["pydantic"] = MockModule()
sys.modules["pydantic_settings"] = MockModule()
sys.modules["rich"] = MockModule()
sys.modules["rich.console"] = MockModule()
sys.modules["rich.logging"] = MockModule()
sys.modules["litellm"] = MockModule()
sys.modules["langgraph"] = MockModule()
sys.modules["langgraph.graph"] = MockModule()
sys.modules["e2b_code_interpreter"] = MockModule()
sys.modules["google"] = MockModule()
sys.modules["google.auth"] = MockModule()

import os
import asyncio
from pathlib import Path
from unittest.mock import patch
from src.services.project_setup.permission_manager import PermissionManager

async def test_fix_permissions_traverses_all_files():
    # Mock data
    mock_root = MagicMock(spec=Path)
    mock_root.exists.return_value = True
    mock_root.is_dir.return_value = True

    mock_file1 = MagicMock(spec=Path)
    mock_file1.is_dir.return_value = False

    mock_dir1 = MagicMock(spec=Path)
    mock_dir1.is_dir.return_value = True

    def rglob_side_effect(pattern):
        return iter([mock_file1, mock_dir1])
    mock_root.rglob.side_effect = rglob_side_effect

    manager = PermissionManager()

    with patch("os.chown") as mock_chown, \
         patch("src.services.project_setup.permission_manager.logger") as mock_logger:

        await manager.fix_permissions(mock_root)

        assert mock_root.rglob.call_count == 2

        assert mock_root.chmod.call_count == 1
        mock_root.chmod.assert_called_with(0o777)

        assert mock_file1.chmod.call_count == 1
        mock_file1.chmod.assert_called_with(0o666)

        assert mock_dir1.chmod.call_count == 1
        mock_dir1.chmod.assert_called_with(0o777)

async def test_fix_permissions_handles_chown():
    mock_root = MagicMock(spec=Path)
    mock_root.exists.return_value = True
    mock_root.is_dir.return_value = True
    mock_root.rglob.return_value = iter([])

    with patch.dict(os.environ, {"HOST_UID": "1000", "HOST_GID": "1000"}), \
         patch("os.chown") as mock_chown, \
         patch("src.services.project_setup.permission_manager.logger"):

        manager = PermissionManager()
        await manager.fix_permissions(mock_root)

        mock_chown.assert_any_call(mock_root, 1000, 1000)

async def test_fix_permissions_ignores_non_existent_path():
    mock_root = MagicMock(spec=Path)
    mock_root.exists.return_value = False

    with patch("src.services.project_setup.permission_manager.logger"):
        manager = PermissionManager()
        await manager.fix_permissions(mock_root)
        mock_root.chmod.assert_not_called()

if __name__ == "__main__":
    print("Running tests...")
    async def run_all():
        try:
            await test_fix_permissions_traverses_all_files()
            print("test_fix_permissions_traverses_all_files: PASSED")
            await test_fix_permissions_handles_chown()
            print("test_fix_permissions_handles_chown: PASSED")
            await test_fix_permissions_ignores_non_existent_path()
            print("test_fix_permissions_ignores_non_existent_path: PASSED")
        except Exception as e:
            import traceback
            traceback.print_exc()
            exit(1)
    asyncio.run(run_all())
