import os
from unittest.mock import patch

from src.utils import get_command_prefix


from unittest.mock import MagicMock

@patch("pathlib.Path.exists")
@patch("pathlib.Path.open")
def test_get_command_prefix_fallback(mock_open: MagicMock, mock_exists: MagicMock) -> None:
    """
    Test that get_command_prefix correctly falls back to 'uv run manage.py'
    when it cannot read the docker environment files.
    """
    # Method 1 fails: .dockerenv does not exist
    mock_exists.return_value = False

    # Method 2 fails: reading /proc/self/cgroup raises FileNotFoundError
    mock_open.side_effect = FileNotFoundError

    # Method 3 fails: DOCKER_CONTAINER is not set
    with patch.dict(os.environ, {}, clear=True):
        assert get_command_prefix() == "uv run manage.py"


@patch("pathlib.Path.exists")
@patch("pathlib.Path.open")
def test_get_command_prefix_permission_error(mock_open: MagicMock, mock_exists: MagicMock) -> None:
    """
    Test that get_command_prefix correctly falls back to 'uv run manage.py'
    when reading /proc/self/cgroup raises a PermissionError.
    """
    # Method 1 fails: .dockerenv does not exist
    mock_exists.return_value = False

    # Method 2 fails: reading /proc/self/cgroup raises PermissionError
    mock_open.side_effect = PermissionError

    # Method 3 fails: DOCKER_CONTAINER is not set
    with patch.dict(os.environ, {}, clear=True):
        assert get_command_prefix() == "uv run manage.py"
