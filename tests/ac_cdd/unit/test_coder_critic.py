import pytest

from src.enums import FlowStatus
from src.nodes.coder_critic import route_coder_critic
from src.state import CycleState

def test_route_coder_critic_completed():
    state = CycleState(cycle_id="1", status=FlowStatus.COMPLETED)
    assert route_coder_critic(state) == "uat_evaluate"

def test_route_coder_critic_retry():
    state = CycleState(cycle_id="1", status=FlowStatus.CODER_RETRY)
    assert route_coder_critic(state) == "coder_session"
