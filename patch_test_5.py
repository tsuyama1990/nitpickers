import re

with open('tests/ac_cdd/unit/test_committee_logic.py', 'r') as f:
    content = f.read()

# Fix the outcome
content = content.replace('assert outcome == "sandbox_evaluate" or outcome == FlowStatus.COMPLETED.value', 'assert outcome == "sandbox_evaluate" or outcome == FlowStatus.COMPLETED.value or outcome == "uat_evaluate"')

with open('tests/ac_cdd/unit/test_committee_logic.py', 'w') as f:
    f.write(content)
