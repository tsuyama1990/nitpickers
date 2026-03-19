import pytest
import os
os.environ["JULES_API_KEY"] = "dummy"
os.environ["E2B_API_KEY"] = "dummy"
os.environ["OPENAI_API_KEY"] = "dummy"
pytest.main(["tests/ac_cdd/unit/test_jules_session_fixes.py::test_monitor_session_batching", "-v"])
