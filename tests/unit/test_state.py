from src.state import CycleState, IntegrationState


def test_cycle_state_backward_compatibility() -> None:
    # Test initialization without new fields works via defaults
    state = CycleState(cycle_id="01")

    assert state.cycle_id == "01"
    assert state.uat.sandbox_artifacts == {}
    assert state.conflict_status is None
    assert state.concurrent_dependencies == []


def test_cycle_state_new_fields_assignment() -> None:
    from src.enums import FlowStatus
    from src.state import UATState

    state = CycleState(
        cycle_id="02",
        uat=UATState(sandbox_artifacts={"coverage": "85%"}),
        conflict_status=FlowStatus.CONFLICT_DETECTED,
        concurrent_dependencies=["01", "03"],
    )

    state.committee.is_refactoring = True
    state.committee.audit_attempt_count = 2

    assert state.uat.sandbox_artifacts == {"coverage": "85%"}
    assert state.conflict_status == FlowStatus.CONFLICT_DETECTED
    assert state.concurrent_dependencies == ["01", "03"]
    assert state.committee.is_refactoring is True
    assert state.committee.audit_attempt_count == 2


def test_integration_state_initialization() -> None:
    from src.domain_models import ConflictRegistryItem

    conflict = ConflictRegistryItem(
        file_path="src/main.py",
        conflict_markers=["<<<<<<<", "=======", ">>>>>>>"],
    )

    state = IntegrationState(
        master_integrator_session_id="session_123", unresolved_conflicts=[conflict]
    )

    assert state.master_integrator_session_id == "session_123"
    assert len(state.unresolved_conflicts) == 1
    assert state.unresolved_conflicts[0].file_path == "src/main.py"


def test_committee_state_audit_attempt_count_not_negative() -> None:
    import pytest
    from pydantic import ValidationError

    from src.state import CommitteeState

    with pytest.raises(ValidationError, match="Input should be greater than or equal to 0"):
        CommitteeState(audit_attempt_count=-1)


def test_cycle_state_new_properties_backward_compatibility() -> None:
    from src.state import CycleState

    state = CycleState(cycle_id="03")

    # Set new properties via CycleState
    state.is_refactoring = True  # type: ignore[attr-defined]
    state.audit_attempt_count = 3  # type: ignore[attr-defined]
    state.current_auditor_index = 2

    # Assert they map correctly to the underlying CommitteeState
    assert state.committee.is_refactoring is True
    assert state.committee.audit_attempt_count == 3
    assert state.committee.current_auditor_index == 2

    # Assert getter works
    assert state.is_refactoring is True  # type: ignore[attr-defined]
    assert state.audit_attempt_count == 3  # type: ignore[attr-defined]
    assert state.current_auditor_index == 2
