import re

with open('tests/ac_cdd/integration/test_mcp_github_read_fallback.py', 'r') as f:
    content = f.read()

# We need to add mock logic to ensure the `git_context` mock is valid.
# In `src/nodes/architect.py`:
# owner, repo_name, _ = await self.jules.git_context.prepare_git_context()

content = content.replace('mock_jules = MagicMock()', '''mock_jules = MagicMock()
    mock_jules.git_context = AsyncMock()
    mock_jules.git_context.prepare_git_context = AsyncMock(return_value=("mockowner", "mockrepo", "mockbranch"))
''')

with open('tests/ac_cdd/integration/test_mcp_github_read_fallback.py', 'w') as f:
    f.write(content)
