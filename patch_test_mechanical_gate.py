with open('tests/unit/test_cycle03_mechanical_gate.py') as f:
    content = f.read()

content = content.replace('''        # We can also just avoid testing _create_proxy_tool internals by mocking it.
        pass''', '''        # We can also just avoid testing _create_proxy_tool internals by mocking it.
        pass''') # dummy replace, will rewrite

with open('tests/unit/test_cycle03_mechanical_gate.py', 'w') as f:
    content = """import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_mechanical_gate_blocks_push_commit():
    \"\"\"
    Verify the Principle of Least Privilege by asserting that read-only nodes
    (e.g., Auditor) are mechanically blocked from accessing or invoking GitHub Write tools.
    \"\"\"
    from src.services.mcp_client_manager import McpClientManager
    mcm = McpClientManager()
    mcm._client = AsyncMock()

    write_tool = AsyncMock()
    write_tool.name = "github_push_commit"

    read_tool = AsyncMock()
    read_tool.name = "github_get_file_content"

    mcm._client.get_tools.return_value = [write_tool, read_tool]

    # We mock _create_proxy_tool since that requires a valid LangChain tool
    with patch.object(mcm, '_create_proxy_tool', side_effect=lambda x, y: x):
        readonly_tools = await mcm.get_readonly_tools("github")
        tool_names = [t.name for t in readonly_tools]

        assert "github_push_commit" not in tool_names
        assert "github_get_file_content" in tool_names
"""
    f.write(content)
