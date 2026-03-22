from src.config import settings
from src.domain_models.review import AuditResult
from src.enums import FlowStatus
from src.nodes.routers import route_auditor, route_final_critic, route_sandbox_evaluate
from src.state import AuditState, CycleState


def test_route_sandbox_evaluate() -> None:
    # Test TDD_FAILED
    state = CycleState(cycle_id="01", status=FlowStatus.TDD_FAILED)
    assert route_sandbox_evaluate(state) == "coder_session"

    # Test READY_FOR_AUDIT, not refactoring
    state = CycleState(cycle_id="01", status=FlowStatus.READY_FOR_AUDIT)
    state.is_refactoring = False
    assert route_sandbox_evaluate(state) == "auditor"

    # Test READY_FOR_AUDIT, is refactoring
    state.is_refactoring = True
    assert route_sandbox_evaluate(state) == "final_critic"

    # Test fallback
    state = CycleState(cycle_id="01", status=FlowStatus.COMPLETED)
    assert route_sandbox_evaluate(state) == "failed"


def test_route_auditor() -> None:
    # Test rejected by None audit result
    state = CycleState(cycle_id="01")
    state.audit_attempt_count = 0
    assert route_auditor(state) == "reject"
    assert state.audit_attempt_count == 1

    # Test rejected by False is_approved
    audit_res = AuditResult(is_approved=False)
    state.audit = AuditState(audit_result=audit_res)
    state.audit_attempt_count = 0
    assert route_auditor(state) == "reject"
    assert state.audit_attempt_count == 1

    # Test rejected by False is_approved max retries
    audit_res = AuditResult(is_approved=False)
    state.audit = AuditState(audit_result=audit_res)
    state.audit_attempt_count = settings.max_audit_retries
    assert route_auditor(state) == "failed"
    assert state.audit_attempt_count == settings.max_audit_retries + 1

    # Test approved, next_auditor
    audit_res_approved = AuditResult(is_approved=True)
    state.audit = AuditState(audit_result=audit_res_approved)
    state.current_auditor_index = 1
    assert route_auditor(state) == "next_auditor"
    assert state.current_auditor_index == 2

    # Test approved, pass_all
    state.current_auditor_index = settings.NUM_AUDITORS
    assert route_auditor(state) == "pass_all"
    assert state.current_auditor_index == settings.NUM_AUDITORS + 1


def test_route_final_critic() -> None:
    # Test coder retry
    state = CycleState(cycle_id="01", status=FlowStatus.CODER_RETRY)
    assert route_final_critic(state) == "reject"

    # Test approved
    state = CycleState(cycle_id="01", status=FlowStatus.COMPLETED)
    assert route_final_critic(state) == "approve"

    # Test fallback
    state = CycleState(cycle_id="01", status=FlowStatus.FAILED)
    assert route_final_critic(state) == "reject"
