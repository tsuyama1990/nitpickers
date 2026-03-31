import pytest
from pydantic import ValidationError

from src.state import CommitteeState, CycleState, IntegrationState


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


def test_committee_state_new_fields() -> None:
    # Test valid initializations
    state = CommitteeState(is_refactoring=True, audit_attempt_count=2, current_auditor_index=3)
    assert state.is_refactoring is True
    assert state.audit_attempt_count == 2
    assert state.current_auditor_index == 3

    # Test default values
    state_default = CommitteeState()
    assert state_default.is_refactoring is False
    assert state_default.audit_attempt_count == 0
    assert state_default.current_auditor_index == 1


def test_committee_state_validators() -> None:
    # Test audit_attempt_count ge=0 constraint
    with pytest.raises(ValidationError):
        CommitteeState(audit_attempt_count=-1)

    # Test current_auditor_index ge=1 constraint
    with pytest.raises(ValidationError):
        CommitteeState(current_auditor_index=0)


def test_cycle_state_backward_compatibility_properties() -> None:
    cycle = CycleState(
        cycle_id="01",
        committee=CommitteeState(
            is_refactoring=True, audit_attempt_count=1, current_auditor_index=2
        ),
    )

    # Test property getters
    assert cycle.get("is_refactoring") is True
    assert cycle.get("audit_attempt_count") == 1
    assert cycle.current_auditor_index == 2

    # Test property setters
    cycle.is_refactoring = False  # type: ignore
    assert cycle.committee.is_refactoring is False
    assert getattr(cycle, "is_refactoring", cycle.committee.is_refactoring) is False

    cycle.audit_attempt_count = 3  # type: ignore
    assert cycle.committee.audit_attempt_count == 3

    cycle.current_auditor_index = 1
    assert cycle.committee.current_auditor_index == 1


def test_cycle_state_legacy_kwargs_mapping() -> None:
    # Test that instantiating CycleState with legacy kwargs maps to the correct nested state
    cycle = CycleState(cycle_id="01", is_refactoring=True, audit_attempt_count=5)  # type: ignore

    assert cycle.committee.is_refactoring is True
    assert cycle.committee.audit_attempt_count == 5
    assert cycle.get("is_refactoring") is True
    assert cycle.get("audit_attempt_count") == 5
