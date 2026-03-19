from src.enums import FlowStatus
from src.nodes.coder_critic import route_coder_critic
from src.state import CycleState


def test_route_coder_critic_routing_rules():
    """
    Scenario ID 05-02 & 05-03 Routing rules:
    - If status is COMPLETED, route to uat_evaluate.
    - If status is CODER_RETRY, route to coder_session.
    """
    state_retry = CycleState(cycle_id="05", status=FlowStatus.CODER_RETRY)
    assert route_coder_critic(state_retry) == "coder_session"

    state_completed = CycleState(cycle_id="05", status=FlowStatus.COMPLETED)
    assert route_coder_critic(state_completed) == "uat_evaluate"
