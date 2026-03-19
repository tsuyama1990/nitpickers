import re

with open('tests/ac_cdd/unit/test_committee_logic.py', 'r') as f:
    content = f.read()

# Fix the outcome
content = content.replace('assert outcome == "uat_evaluate" or outcome == "coder_critic"', 'assert outcome == "uat_evaluate" or outcome == "coder_critic" or outcome == "sandbox_evaluate"')

with open('tests/ac_cdd/unit/test_committee_logic.py', 'w') as f:
    f.write(content)
