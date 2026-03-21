import re
with open('tests/unit/test_mcp_client_manager.py', 'r') as f:
    content = f.read()

content = re.sub(r'manager = McpClientManager\(config=config\)\n    manager = McpClientManager\(config=config\)\n    manager = McpClientManager\(config=config\)\n    manager = McpClientManager\(config=config\)', 'manager = McpClientManager(config=config)', content)
content = content.replace('manager = McpClientManager(configs=[config])', 'manager = McpClientManager(config=config)')

with open('tests/unit/test_mcp_client_manager.py', 'w') as f:
    f.write(content)
