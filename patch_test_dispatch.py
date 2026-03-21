with open('tests/ac_cdd/integration/test_mcp_jules_session_dispatch.py') as f:
    content = f.read()

content = content.replace('''    # Mock AST to avoid importing McpClientManager
    # Because ASTAnalyzer is not actually failing, it's McpClientManager in the use case that throws error if it's there
    with patch("src.nodes.global_refactor.RefactorUsecase") as MockUsecase:''', '''    # Just test that the node processes it properly.
    import sys

    with patch("src.nodes.global_refactor.RefactorUsecase") as MockUsecase:''')

with open('tests/ac_cdd/integration/test_mcp_jules_session_dispatch.py', 'w') as f:
    f.write(content)
