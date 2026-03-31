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


def test_cycle_state_new_properties() -> None:
    state = CycleState(cycle_id="03")

    # Test default values via new properties
    assert state.is_refactoring is False  # type: ignore
    assert state.audit_attempt_count == 0  # type: ignore

    # Test setters
    state.is_refactoring = True  # type: ignore
    state.audit_attempt_count = 1  # type: ignore

    assert state.committee.is_refactoring is True
    assert state.committee.audit_attempt_count == 1

    # Test getting
    assert state.is_refactoring is True  # type: ignore
    assert state.audit_attempt_count == 1  # type: ignore


def test_audit_attempt_count_validation() -> None:
    import pytest
    from pydantic import ValidationError

    state = CycleState(cycle_id="04")

    with pytest.raises(ValidationError, match="audit_attempt_count"):
        state.audit_attempt_count = -1  # type: ignore
