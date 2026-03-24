from src.config import settings
from src.enums import FlowStatus
from src.state import CycleState


def route_coder_critic(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == FlowStatus.CODER_RETRY:
        return "coder_session"
    return settings.node_uat_evaluate


def check_coder_outcome(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status in {FlowStatus.FAILED, FlowStatus.ARCHITECT_FAILED}:
        return str(FlowStatus.FAILED.value)

    if getattr(state, "final_fix", False):
        return str(FlowStatus.COMPLETED.value)

    if status == FlowStatus.CODER_RETRY:
        return "coder_session"

    if status == FlowStatus.READY_FOR_AUDIT:
        # Route to self_critic only on the first attempt
        if (
            state.committee.iteration_count <= 1
            and state.committee.audit_attempt_count == 0
            and state.committee.current_auditor_index == 1
        ):
            return "self_critic"
        return settings.node_sandbox_evaluate
    return settings.node_uat_evaluate


def route_sandbox_evaluate(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == FlowStatus.TDD_FAILED:
        return "coder_session"

    if status == FlowStatus.READY_FOR_AUDIT:
        if state.committee.is_refactoring:
            return "final_critic"
        return "auditor"

    return "failed"


def route_auditor(state: CycleState) -> str:
    # Use explicit audit_result field from state.audit based on trace inspection
    is_approved = False
    if state.audit.audit_result is not None:
        is_approved = state.audit.audit_result.is_approved

    if not is_approved:
        state.committee.audit_attempt_count += 1
        if state.committee.audit_attempt_count > settings.max_audit_retries:
            return "failed"
        return "reject"

    # Reset attempt count on pass
    state.committee.audit_attempt_count = 0
    state.committee.current_auditor_index += 1
    if state.committee.current_auditor_index > settings.NUM_AUDITORS:
        return "pass_all"
    return "next_auditor"


def route_final_critic(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == FlowStatus.COMPLETED:
        return "approve"
    return "reject"


def route_qa(state: CycleState) -> str:
    status = getattr(state, "status", None)
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
