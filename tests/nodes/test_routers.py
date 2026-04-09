from src.config import settings
from src.domain_models import AuditResult
from src.enums import FlowStatus
from src.nodes.routers import route_auditor, route_final_critic, route_sandbox_evaluate
from src.state import CycleState


def test_route_sandbox_evaluate_failed() -> None:
    state = CycleState(cycle_id="01")
    state.status = FlowStatus.FAILED
    assert (
        route_sandbox_evaluate(state) == "impl_coder_node"
    )  # Looking at the code for green phase routing, but wait, if it's failed in Green phase, it goes to impl_coder_node according to the code, but SPEC says: "If state.get("sandbox_status") == "failed", return "failed"." I will assert the SPEC behavior to make it fail against current code.

    # Asserting spec behavior to force test failure on current code
    assert route_sandbox_evaluate(state) == "failed"


def test_route_sandbox_evaluate_refactoring() -> None:
    state = CycleState(cycle_id="01")
    state.status = FlowStatus.READY_FOR_AUDIT
    state.committee.is_refactoring = True
    assert route_sandbox_evaluate(state) == "final_critic"


def test_route_sandbox_evaluate_auditor() -> None:
    state = CycleState(cycle_id="01")
    state.status = FlowStatus.READY_FOR_AUDIT
    state.committee.is_refactoring = False
    assert route_sandbox_evaluate(state) == "auditor"


def test_route_auditor_reject() -> None:
    state = CycleState(cycle_id="01")
    state.audit.audit_result = AuditResult(is_approved=False, status="Reject")
    state.committee.audit_attempt_count = 0
    route = route_auditor(state)
    assert route == "reject"
    assert state.committee.audit_attempt_count == 1


def test_route_auditor_reject_fallback() -> None:
    state = CycleState(cycle_id="01")
    state.audit.audit_result = AuditResult(is_approved=False, status="Reject")
    state.committee.audit_attempt_count = settings.max_audit_retries
    route = route_auditor(state)
    assert route == "requires_pivot"
    assert state.committee.audit_attempt_count == settings.max_audit_retries + 1


def test_route_auditor_approve_next() -> None:
    state = CycleState(cycle_id="01")
    state.audit.audit_result = AuditResult(is_approved=True, status="Approve")
    state.committee.current_auditor_index = 1
    state.committee.audit_attempt_count = 2
    route = route_auditor(state)
    assert route == "next_auditor"
    assert state.committee.audit_attempt_count == 0
    assert state.committee.current_auditor_index == 2


def test_route_auditor_approve_pass_all() -> None:
    state = CycleState(cycle_id="01")
    state.audit.audit_result = AuditResult(is_approved=True, status="Approve")
    state.committee.current_auditor_index = settings.NUM_AUDITORS
    route = route_auditor(state)
    assert route == "pass_all"
    assert state.committee.current_auditor_index == settings.NUM_AUDITORS + 1


def test_route_final_critic() -> None:
    state = CycleState(cycle_id="01")

    state.status = FlowStatus.COMPLETED
    assert route_final_critic(state) == "approve"

    state.status = FlowStatus.FAILED
    assert route_final_critic(state) == "reject"
