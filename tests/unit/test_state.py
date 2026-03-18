from src.state import CycleState, IntegrationState


def test_cycle_state_backward_compatibility() -> None:
    # Test initialization without new fields works via defaults
    state = CycleState(cycle_id="test_backward_compatible")

    assert state.cycle_id == "test_backward_compatible"
    assert state.sandbox_artifacts == {}
    assert state.conflict_status is None
    assert state.concurrent_dependencies == []


def test_cycle_state_new_fields_assignment() -> None:
    from src.enums import FlowStatus

    state = CycleState(
        cycle_id="test_new_fields",
        sandbox_artifacts={"coverage": "85%"},
        conflict_status=FlowStatus.CONFLICT_DETECTED,
        concurrent_dependencies=["cycle_01", "cycle_02"]
    )

    assert state.sandbox_artifacts == {"coverage": "85%"}
    assert state.conflict_status == FlowStatus.CONFLICT_DETECTED
    assert state.concurrent_dependencies == ["cycle_01", "cycle_02"]


def test_integration_state_initialization() -> None:
    from src.domain_models import ConflictRegistryItem

    conflict = ConflictRegistryItem(
        file_path="src/main.py",
        conflict_markers=["<<<<<<<", "=======", ">>>>>>>"],
    )

    state = IntegrationState(
        master_integrator_session_id="session_123",
        unresolved_conflicts=[conflict]
    )

    assert state.master_integrator_session_id == "session_123"
    assert len(state.unresolved_conflicts) == 1
    assert state.unresolved_conflicts[0].file_path == "src/main.py"
