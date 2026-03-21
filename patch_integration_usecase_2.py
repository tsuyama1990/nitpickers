with open('src/services/integration_usecase.py') as f:
    content = f.read()

content = content.replace('''        message_history: list[dict[str, str]] = []''', '')
content = content.replace('''            async with self.mcp_client as client:''', '''            async with self.mcp_client as _client:''')

with open('src/services/integration_usecase.py', 'w') as f:
    f.write(content)
