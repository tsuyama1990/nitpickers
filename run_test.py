import pytest
import subprocess
print(subprocess.run(["uv", "run", "pytest", "tests/unit/test_self_critic_evaluator.py", "tests/uat/verify_cycle_02_domain_logic.py"], capture_output=True, text=True).stdout)
