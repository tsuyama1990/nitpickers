import glob

for test_file in glob.glob('tests/**/*.py', recursive=True):
    with open(test_file) as f:
        content = f.read()

    # Move pytestmark imports
    if 'pytestmark =' in content:
        lines = content.split('\n')
        pytestmark_lines = [l for l in lines if l.startswith('pytestmark =')]
        non_pytestmark_lines = [l for l in lines if not l.startswith('pytestmark =')]

        # Insert them right after imports
        # Find last import
        last_import_idx = 0
        for i, l in enumerate(non_pytestmark_lines):
            if l.startswith('import ') or l.startswith('from '):
                last_import_idx = i

        new_lines = non_pytestmark_lines[:last_import_idx+1] + pytestmark_lines + non_pytestmark_lines[last_import_idx+1:]
        content = '\n'.join(new_lines)

        with open(test_file, 'w') as f:
            f.write(content)
