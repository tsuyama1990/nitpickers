from typing import Any

import pytest
from pydantic import ValidationError

from src.domain_models import FileModification, FixPlan, UATResult
from src.state import CycleState


def test_fix_plan_validation() -> None:
    # Valid instantiation
    plan = FixPlan(
        modifications=[
            FileModification(filepath="foo.py", explanation="fix bug", diff_block="some diff")
        ]
    )
    assert plan.modifications[0].filepath == "foo.py"

    # Missing fields should raise ValidationError
    payload: Any = {"filepath": "foo.py", "explanation": "fix bug"}
    with pytest.raises(ValidationError) as exc:
        FixPlan(modifications=[payload])
    assert "diff_block" in str(exc.value)


def test_uat_result_validation() -> None:
    # Valid instantiation
    res = UATResult(
        exit_code=1, stderr="error", screenshot_path="path.png", dom_trace_path="trace.txt"
    )
    assert res.exit_code == 1
    assert res.screenshot_path == "path.png"

    # Empty path should raise ValidationError
    with pytest.raises(ValidationError) as exc:
        UATResult(exit_code=1, stderr="error", screenshot_path="   ")
    assert "Path cannot be empty if provided" in str(exc.value)


def test_cycle_state_backward_compatibility() -> None:
    # State initializes without UAT fields and defaults to None/0
    state = CycleState(cycle_id="cycle-1")
    assert state.uat_exit_code == 0
    assert state.uat_artifacts is None
    assert state.current_fix_plan is None
