import re

with open('tests/ac_cdd/unit/test_committee_logic.py', 'r') as f:
    content = f.read()

# Fix the outcome
content = content.replace('assert outcome == "uat_evaluate" or outcome == "coder_critic" or outcome == "sandbox_evaluate"', 'assert outcome == "sandbox_evaluate" or outcome == FlowStatus.COMPLETED.value')

with open('tests/ac_cdd/unit/test_committee_logic.py', 'w') as f:
    f.write(content)
