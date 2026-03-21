import re

files_to_fix = ['src/services/mcp_client_manager.py', 'tests/ac_cdd/integration/test_git_robustness.py']

for file in files_to_fix:
    with open(file) as f:
        content = f.read()

    # Just aggressively strip type ignores that specify error codes to plain type ignore
    content = re.sub(r'# type: ignore\[[^\]]+\]', '# type: ignore', content)

    with open(file, 'w') as f:
        f.write(content)
