with open('tests/unit/test_permission_manager.py', 'r') as f:
    content = f.read()

content = content.replace('''# Now we can import the manager
import pytest

from src.services.project_setup.permission_manager import PermissionManager  # noqa: E402''', '''import pytest
from src.services.project_setup.permission_manager import PermissionManager''')

with open('tests/unit/test_permission_manager.py', 'w') as f:
    f.write(content)
