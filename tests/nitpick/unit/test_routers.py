from src.domain_models.review import AuditResult
from src.enums import FlowStatus
from src.nodes.routers import (
    route_auditor,
    route_sandbox_evaluate,
)
from src.state import AuditState, CycleState


def test_route_sandbox_evaluate() -> None:
    # Test RED phase failures go to impl_coder_node
    state = CycleState(cycle_id="01", status=FlowStatus.TDD_FAILED)
    state.test.tdd_phase = "red"
    assert route_sandbox_evaluate(state) == "impl_coder_node"

    # Test RED phase success (incorrectly passes) goes back to test_coder_node
    state = CycleState(cycle_id="01", status=FlowStatus.READY_FOR_AUDIT)
    state.test.tdd_phase = "red"
    assert route_sandbox_evaluate(state) == "test_coder_node"

    # Test GREEN phase TDD_FAILED goes to impl_coder_node
    state = CycleState(cycle_id="01", status=FlowStatus.TDD_FAILED)
    state.test.tdd_phase = "green"
    assert route_sandbox_evaluate(state) == "impl_coder_node"

    # Test GREEN phase READY_FOR_AUDIT, not refactoring
    state = CycleState(cycle_id="01", status=FlowStatus.READY_FOR_AUDIT)
    state.test.tdd_phase = "green"
    state.committee.is_refactoring = False
    assert route_sandbox_evaluate(state) == "auditor"

    # Test GREEN phase READY_FOR_AUDIT, is refactoring
    state.committee.is_refactoring = True
    assert route_sandbox_evaluate(state) == "final_critic"

    # Test GREEN phase fallback
    state = CycleState(cycle_id="01", status=FlowStatus.COMPLETED)
    state.test.tdd_phase = "green"
    assert route_sandbox_evaluate(state) == "impl_coder_node"


def test_route_auditor() -> None:
    # Test rejected by None audit result
    state = CycleState(cycle_id="01")
    assert route_auditor(state) == "reject"

    # Test rejected by False is_approved
    audit_res = AuditResult(is_approved=False)
    state.audit = AuditState(audit_result=audit_res)
    assert route_auditor(state) == "reject"

