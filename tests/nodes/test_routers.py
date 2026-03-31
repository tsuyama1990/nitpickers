from src.config import settings
from src.domain_models import AuditResult
from src.enums import FlowStatus
from src.nodes.routers import route_auditor, route_final_critic, route_sandbox_evaluate
from src.state import AuditState, CommitteeState, CycleState


def test_route_sandbox_evaluate() -> None:
    # Test failed state
    state_failed = CycleState(cycle_id="01", status=FlowStatus.FAILED)
    assert route_sandbox_evaluate(state_failed) == "impl_coder_node"

    # Test is_refactoring=True logic
    state_refactoring = CycleState(
        cycle_id="01",
        status=FlowStatus.READY_FOR_AUDIT,
        committee=CommitteeState(is_refactoring=True),
    )
    assert route_sandbox_evaluate(state_refactoring) == "final_critic"

    # Test normal success
    state_success = CycleState(
        cycle_id="01",
        status=FlowStatus.READY_FOR_AUDIT,
        committee=CommitteeState(is_refactoring=False),
    )
    assert route_sandbox_evaluate(state_success) == "auditor"


def test_route_auditor() -> None:
    # Test rejection loop
    state_reject = CycleState(
        cycle_id="01",
        committee=CommitteeState(audit_attempt_count=0, current_auditor_index=1),
        audit=AuditState(audit_result=AuditResult(is_approved=False)),
    )

    assert route_auditor(state_reject) == "reject"
    assert state_reject.committee.audit_attempt_count == 1

    # Test reaching max retries
    state_max_retries = CycleState(
        cycle_id="01",
        committee=CommitteeState(
            audit_attempt_count=settings.max_audit_retries, current_auditor_index=1
        ),
        audit=AuditState(audit_result=AuditResult(is_approved=False)),
    )

    assert route_auditor(state_max_retries) == "requires_pivot"
    assert state_max_retries.committee.audit_attempt_count == settings.max_audit_retries + 1

    # Test approval routing
    state_approve = CycleState(
        cycle_id="01",
        committee=CommitteeState(audit_attempt_count=2, current_auditor_index=1),
        audit=AuditState(audit_result=AuditResult(is_approved=True)),
    )

    # Needs to transition to next_auditor since index <= NUM_AUDITORS
    assert route_auditor(state_approve) == "next_auditor"
    assert state_approve.committee.current_auditor_index == 2
    assert state_approve.committee.audit_attempt_count == 0  # Count should reset

    # Test approval passing all auditors
    state_pass_all = CycleState(
        cycle_id="01",
        committee=CommitteeState(
            audit_attempt_count=0, current_auditor_index=settings.NUM_AUDITORS
        ),
        audit=AuditState(audit_result=AuditResult(is_approved=True)),
    )

    assert route_auditor(state_pass_all) == "pass_all"
    assert state_pass_all.committee.current_auditor_index == settings.NUM_AUDITORS + 1


def test_route_final_critic() -> None:
    # Test approval
    state_approve = CycleState(cycle_id="01", status=FlowStatus.COMPLETED)
    assert route_final_critic(state_approve) == "approve"

    # Test rejection
    state_reject = CycleState(cycle_id="01", status=FlowStatus.REJECTED)
    assert route_final_critic(state_reject) == "reject"
