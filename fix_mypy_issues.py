import re

with open("tests/ac_cdd/integration/test_mcp_github_read_fallback.py", "r") as f:
    content = f.read()

content = content.replace("def __init__(self, msg) -> None:", "def __init__(self, msg: Any) -> None:")
content = content.replace("def __init__(self, choices) -> None:", "def __init__(self, choices: Any) -> None:")
content = content.replace("async def mock_acompletion(*args, **kwargs):", "async def mock_acompletion(*args: Any, **kwargs: Any) -> Any:")
content = content.replace("def model_dump(self):", "def model_dump(self) -> dict[str, Any]:")
content = content.replace("async def mock_tool_arun(*args, **kwargs):", "async def mock_tool_arun(*args: Any, **kwargs: Any) -> str:")
content = content.replace("def mock_tool_run(*args, **kwargs):", "def mock_tool_run(*args: Any, **kwargs: Any) -> str:")
content = "from typing import Any\n" + content

with open("tests/ac_cdd/integration/test_mcp_github_read_fallback.py", "w") as f:
    f.write(content)
