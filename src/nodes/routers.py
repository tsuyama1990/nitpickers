from src.config import settings
from src.enums import FlowStatus
from src.state import CycleState


def check_coder_outcome(state: CycleState) -> str:
    status = getattr(state, "status", None)

    if status in {FlowStatus.FAILED, FlowStatus.ARCHITECT_FAILED}:
        return str(FlowStatus.FAILED.value)

    if status == FlowStatus.COMPLETED or getattr(state, "final_fix", False):
        return str(FlowStatus.COMPLETED.value)

    # Always route to implementation node, bypassing the TDD test loop
    if status == FlowStatus.CODER_RETRY:
        return "impl_coder_node"

    if status == FlowStatus.READY_FOR_AUDIT:
        return settings.node_sandbox_evaluate

    return settings.node_sandbox_evaluate


def route_sandbox_evaluate(state: CycleState) -> str:
    status = getattr(state, "status", None)

    # Simplified routing enforcing 20-step linear path
    if status in {FlowStatus.FAILED, FlowStatus.TDD_FAILED}:
        return "impl_coder_node"

    if status == FlowStatus.POST_AUDIT_REFACTOR:
        return "impl_coder_node"

    if status == FlowStatus.READY_FOR_AUDIT:
        return "auditor"

    return "impl_coder_node"


def route_auditor(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == FlowStatus.REQUIRES_PIVOT:
        state.committee.audit_attempt_count += 1
        return "requires_pivot"

    # Use explicit audit_result field from state.audit based on trace inspection
    is_approved = False
    if state.audit.audit_result is not None:
        is_approved = state.audit.audit_result.is_approved

    if not is_approved:
        state.committee.audit_attempt_count += 1
        if state.committee.audit_attempt_count > settings.max_audit_retries:
            return "requires_pivot"
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


def route_architect_session(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == FlowStatus.ARCHITECT_SESSION_COMPLETED:
        return "architect_critic"
    return "end"


def route_architect_critic(state: CycleState) -> str:
    status = getattr(state, "status", None)
    if status == FlowStatus.ARCHITECT_CRITIC_REJECTED:
        return "architect_session"
    if status == FlowStatus.ARCHITECT_COMPLETED:
        return "end"
    if status == FlowStatus.ARCHITECT_FAILED:
        return "end"
    return "end"
