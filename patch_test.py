with open('tests/unit/test_cycle03_mechanical_gate.py') as f:
    content = f.read()

content = content.replace('src.services.auditor_usecase.McpClientManager', 'src.services.mcp_client_manager.McpClientManager')

with open('tests/unit/test_cycle03_mechanical_gate.py', 'w') as f:
    f.write(content)
