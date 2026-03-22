from src.config import settings
from src.enums import FlowStatus
from src.state import CycleState


def check_coder_outcome(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status in {FlowStatus.FAILED, FlowStatus.ARCHITECT_FAILED}:
        return str(FlowStatus.FAILED.value)

    if getattr(state, "final_fix", False):
        return str(FlowStatus.COMPLETED.value)

    if status == FlowStatus.CODER_RETRY:
        return settings.node_sandbox_evaluate
    if status == FlowStatus.READY_FOR_AUDIT:
        # Route to self_critic only on the first attempt
        if state.iteration_count <= 1 and state.audit_attempt_count == 0 and state.current_auditor_index == 1:
            return "self_critic"
        return settings.node_sandbox_evaluate
    return settings.node_uat_evaluate


def route_sandbox_evaluate(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == FlowStatus.TDD_FAILED:
        return "coder_session"

    if status == FlowStatus.READY_FOR_AUDIT:
        if state.is_refactoring:
            return "final_critic"
        return "auditor"

    return "failed"


def route_auditor(state: CycleState) -> str:
    # Use explicit audit_result field from state.audit based on trace inspection
    is_approved = False
    if state.audit.audit_result is not None:
        is_approved = state.audit.audit_result.is_approved

    if not is_approved:
        state.audit_attempt_count += 1
        if state.audit_attempt_count > settings.max_audit_retries:
            return "failed"
        return "reject"

    # Reset attempt count on pass
    state.audit_attempt_count = 0
    state.current_auditor_index += 1
    if state.current_auditor_index > settings.NUM_AUDITORS:
        return "pass_all"
    return "next_auditor"


def route_final_critic(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == FlowStatus.CODER_RETRY:
        return "reject"
    if status == FlowStatus.COMPLETED:
        return "approve"
    return "reject"


def check_audit_outcome(_state: CycleState) -> str:
    return "rejected_retry"


def route_committee(state: CycleState) -> str:
    status = getattr(state, "status", None)
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
    status = getattr(state, "status", None)
    if status == FlowStatus.START_REFACTOR:
        return "coder_session"
    if status == FlowStatus.COMPLETED:
        return "end"
    if status == FlowStatus.UAT_FAILED:
        from src.utils import logger

        retry_count = getattr(state, "uat_retry_count", 0)
        max_retries = getattr(settings.uat, "max_retries", 3)
        if retry_count >= max_retries:
            logger.error(f"UAT Failed {retry_count} times. Halting to prevent infinite loop.")
            return "failed"
        return "auditor"
    return "end"


def route_coder_critic(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == FlowStatus.CODER_RETRY:
        return "coder_session"
    return settings.node_uat_evaluate


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
