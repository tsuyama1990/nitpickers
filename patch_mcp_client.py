with open('src/services/mcp_client_manager.py') as f:
    content = f.read()

content = content.replace('args_schema=tool.args_schema,  # type: ignore', 'args_schema=tool.args_schema,')

with open('src/services/mcp_client_manager.py', 'w') as f:
    f.write(content)
