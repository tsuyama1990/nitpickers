with open('src/service_container.py') as f:
    content = f.read()

content = content.replace('''from dataclasses import dataclass''', '''from dataclasses import dataclass\nfrom typing import Any''')

with open('src/service_container.py', 'w') as f:
    f.write(content)
