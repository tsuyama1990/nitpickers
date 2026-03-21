with open('tests/ac_cdd/integration/test_mcp_jules_session_dispatch.py') as f:
    content = f.read()

content = content.replace('''    with patch("src.nodes.global_refactor.RefactorUsecase") as MockUsecase:''', '''    with patch("src.nodes.global_refactor.RefactorUsecase"):''')

with open('tests/ac_cdd/integration/test_mcp_jules_session_dispatch.py', 'w') as f:
    f.write(content)
