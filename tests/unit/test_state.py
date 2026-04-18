from src.state import CycleState, IntegrationState


def test_cycle_state_backward_compatibility() -> None:
    # Test initialization without new fields works via defaults
    state = CycleState(cycle_id="01")

    assert state.cycle_id == "01"
    assert state.uat.sandbox_artifacts == {}
    assert state.conflict_status is None
    assert state.concurrent_dependencies == []


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
