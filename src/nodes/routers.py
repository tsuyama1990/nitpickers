from src.config import settings
from src.enums import FlowStatus
from src.state import CycleState


def check_coder_outcome(state: CycleState) -> str:
    status = state.get("status")
    if status in {FlowStatus.FAILED, FlowStatus.ARCHITECT_FAILED}:
        return str(FlowStatus.FAILED.value)

    if state.get("final_fix", False):
        return str(FlowStatus.COMPLETED.value)

    if status == FlowStatus.CODER_RETRY:
        return str(FlowStatus.CODER_RETRY.value)
    if status == FlowStatus.READY_FOR_AUDIT:
        return settings.node_sandbox_evaluate
    return settings.node_uat_evaluate


def route_sandbox_evaluate(state: CycleState) -> str:
    status = state.get("status")
    if status == FlowStatus.READY_FOR_AUDIT:
        return "auditor"
    if status == FlowStatus.TDD_FAILED:
        return "coder_session"
    return "failed"


def check_audit_outcome(_state: CycleState) -> str:
    return "rejected_retry"


def route_committee(state: CycleState) -> str:
    status = state.get("status")
    if status == FlowStatus.NEXT_AUDITOR:
        return "auditor"
    if status == FlowStatus.CYCLE_APPROVED:
        return settings.node_coder_critic
    if status in {
        FlowStatus.RETRY_FIX,
        FlowStatus.WAIT_FOR_JULES_COMPLETION,
        FlowStatus.POST_AUDIT_REFACTOR,
    }:
        return "coder_session"
    return "failed"


def route_uat(state: CycleState) -> str:
    status = state.get("status")
    if status == FlowStatus.START_REFACTOR:
        return "coder_session"
    if status == FlowStatus.COMPLETED:
        return "end"
    return "end"


def route_coder_critic(state: CycleState) -> str:
    status = state.get("status")
    if status == FlowStatus.CODER_RETRY:
        return "coder_session"
    return settings.node_uat_evaluate


def route_qa(state: CycleState) -> str:
    status = state.get("status")
    if status == FlowStatus.APPROVED:
        return "end"
    if status == FlowStatus.REJECTED:
        return "retry_fix"
    return "failed"


def route_architect_critic(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == "architect_completed":
        return "end"
    if status == "architect_failed":
        return "end"
    if status == "architect_critic_rejected":
        return "architect_session"
    return "end"
