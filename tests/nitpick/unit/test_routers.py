from src.domain_models.review import AuditResult
from src.enums import FlowStatus
from src.nodes.routers import route_auditor, route_final_critic, route_sandbox_evaluate
from src.state import AuditState, CycleState


def test_route_sandbox_evaluate() -> None:
    # Test failed via sandbox_status property
    state = CycleState(cycle_id="01")
    object.__setattr__(state, "sandbox_status", "failed")
    assert route_sandbox_evaluate(state) == "coder_session"

    # Test TDD_FAILED
    state = CycleState(cycle_id="01")
    state.status = FlowStatus.TDD_FAILED
    assert route_sandbox_evaluate(state) == "coder_session"

    # Test READY_FOR_AUDIT, not refactoring
    state = CycleState(cycle_id="01")
    state.status = FlowStatus.READY_FOR_AUDIT
    state.is_refactoring = False
    assert route_sandbox_evaluate(state) == "auditor_node"

    # Test READY_FOR_AUDIT, is refactoring
    state = CycleState(cycle_id="01")
    state.status = FlowStatus.READY_FOR_AUDIT
    state.is_refactoring = True
    assert route_sandbox_evaluate(state) == "final_critic_node"


def test_route_auditor() -> None:
    # Test rejected by None audit result
    state = CycleState(cycle_id="01")
    object.__setattr__(state.committee, "audit_attempt_count", 0)
    assert route_auditor(state) == "reject"
    assert state.audit_attempt_count == 1

    # Test rejected by False is_approved
    audit_res = AuditResult(is_approved=False)
    state.audit = AuditState(audit_result=audit_res)
    object.__setattr__(state.committee, "audit_attempt_count", 0)
    assert route_auditor(state) == "reject"
    assert state.audit_attempt_count == 1

    # Test approved, next_auditor
    audit_res_approved = AuditResult(is_approved=True)
    state.audit = AuditState(audit_result=audit_res_approved)
    object.__setattr__(state.committee, "current_auditor_index", 1)
    assert route_auditor(state) == "next_auditor"
    assert state.current_auditor_index == 2

    # Test approved, pass_all
    object.__setattr__(state.committee, "current_auditor_index", 3)
    assert route_auditor(state) == "pass_all"
    assert state.current_auditor_index == 4


def test_route_final_critic() -> None:
    # Test coder retry / reject
    state = CycleState(cycle_id="01")
    state.status = FlowStatus.CODER_RETRY
    assert route_final_critic(state) == "reject"

    state = CycleState(cycle_id="01")
    object.__setattr__(state, "status", "reject")
    assert route_final_critic(state) == "reject"

    # Test approved
    state = CycleState(cycle_id="01")
    state.status = FlowStatus.COMPLETED
    assert route_final_critic(state) == "approve"

    state = CycleState(cycle_id="01")
    object.__setattr__(state, "status", "approve")
    assert route_final_critic(state) == "approve"

    # Test fallback
    state = CycleState(cycle_id="01")
    state.status = FlowStatus.FAILED
    assert route_final_critic(state) == "reject"
