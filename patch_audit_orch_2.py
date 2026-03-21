with open('src/services/audit_orchestrator.py') as f:
    content = f.read()

import re

content = re.sub(r'    async def _wait_for_new_plan.*', '', content, flags=re.DOTALL)

with open('src/services/audit_orchestrator.py', 'w') as f:
    f.write(content)
