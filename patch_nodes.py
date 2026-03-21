for file_path in ['src/graph.py', 'src/graph_nodes.py', 'src/service_container.py', 'src/services/workflow.py']:
    with open(file_path) as f:
        content = f.read()

    content = content.replace('''jules: JulesClient''', '''jules: Any''')
    content = content.replace('''jules_client: JulesClient''', '''jules_client: Any''')
    content = content.replace('''jules=JulesClient(),''', '''jules=None,''')
    content = content.replace('''JulesClient()''', '''None''')

    if file_path == 'src/service_container.py':
        content = content.replace('''from typing import TypedDict''', '''from typing import TypedDict, Any''')

    with open(file_path, 'w') as f:
        f.write(content)
