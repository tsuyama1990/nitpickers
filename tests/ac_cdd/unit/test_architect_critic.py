from dev_src.ac_cdd_core.enums import FlowStatus
from dev_src.ac_cdd_core.state import CycleState
from src.domain_models.critic import CriticFeedbackItem, CriticResponse


def test_critic_response_schema_valid() -> None:
    response = CriticResponse(
        is_passed=True,
        summary="Everything looks good.",
        feedback=[]
    )
    assert response.is_passed is True
    assert len(response.feedback) == 0


def test_critic_response_schema_invalid() -> None:
    response = CriticResponse(
        is_passed=False,
        summary="Missing interface contract.",
        feedback=[
            CriticFeedbackItem(
                category="Interface Contract Missing",
                severity="fatal",
                issue_description="No function signature defined.",
                concrete_fix="Add def my_func(a: int) -> str:"
            )
        ]
    )
    assert response.is_passed is False
    assert len(response.feedback) == 1
    assert response.feedback[0].category == "Interface Contract Missing"


def test_cycle_state_critic_fields() -> None:
    state = CycleState(cycle_id="test")
    assert state.is_architecture_locked is False
    assert state.critic_feedback == []

    state.is_architecture_locked = True
    state.critic_feedback = ["missing return type"]
    assert state.is_architecture_locked is True
    assert len(state.critic_feedback) == 1

def test_enums() -> None:
    assert FlowStatus.CRITIC_REJECTED.value == "critic_rejected"
    assert FlowStatus.ARCHITECTURE_APPROVED.value == "architecture_approved"
