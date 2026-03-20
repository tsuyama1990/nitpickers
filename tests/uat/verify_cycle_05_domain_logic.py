from collections.abc import Callable
from typing import Any

import marimo

__generated_with = "0.10.19"
app = marimo.App(width="medium")


@app.cell(name="setup_imports")
def setup_imports() -> tuple[Any, ...]:
    import pytest

    from src.domain_models.uat_execution_state import UatExecutionState
    from src.enums import FlowStatus
    from src.nodes.routers import route_uat
    from src.state import CycleState

    return CycleState, FlowStatus, UatExecutionState, pytest, route_uat


@app.cell(name="run_routing_tests")
def run_routing_tests(
    CycleState: Any,  # noqa: N803
    FlowStatus: Any,  # noqa: N803
    UatExecutionState: Any,  # noqa: N803
    route_uat: Callable[[Any], str],
) -> tuple[Any, ...]:
    def test_route_uat_routing_rules() -> None:
        """
        Scenario ID 05-02 & 05-03 Routing rules:
        - If status is COMPLETED, route to end.
        - If status is UAT_FAILED, route to auditor.
        """
        state_retry = CycleState(cycle_id="05", status=FlowStatus.UAT_FAILED)
        assert route_uat(state_retry) == "auditor"

        state_completed = CycleState(cycle_id="05", status=FlowStatus.COMPLETED)
        assert route_uat(state_completed) == "end"

        state_refactor = CycleState(cycle_id="05", status=FlowStatus.START_REFACTOR)
        assert route_uat(state_refactor) == "coder_session"

    test_route_uat_routing_rules()
    return (test_route_uat_routing_rules,)


if __name__ == "__main__":
    app.run()
