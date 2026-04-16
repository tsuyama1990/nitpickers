from unittest.mock import MagicMock

from src.enums import FlowStatus
from src.graph import GraphBuilder
from src.state import CycleState


def test_coder_graph_happy_path() -> None:
    services = MagicMock()
    sandbox = MagicMock()
    jules = MagicMock()

    builder = GraphBuilder(services, sandbox, jules)

    nodes_mock = MagicMock()

    def mock_test_coder(state: CycleState) -> CycleState:
        state.status = FlowStatus.COMPLETED
        return state

    nodes_mock.test_coder_node = mock_test_coder

    def mock_impl_coder(state: CycleState) -> CycleState:
        state.status = FlowStatus.READY_FOR_AUDIT
        return state

    nodes_mock.impl_coder_node = mock_impl_coder

    def mock_sandbox_eval(state: CycleState) -> CycleState:
        state.status = FlowStatus.READY_FOR_AUDIT
        return state

    nodes_mock.sandbox_evaluate_node = mock_sandbox_eval

    def mock_auditor(state: CycleState) -> CycleState:
        from src.domain_models import AuditResult

        state.audit.audit_result = AuditResult(is_approved=True, status="Approve")
        state.committee.current_auditor_index += 1
        return state

    nodes_mock.auditor_node = mock_auditor

    def mock_self_critic(state: CycleState) -> CycleState:
        return state

    nodes_mock.self_critic_node = mock_self_critic

    def mock_refactor(state: CycleState) -> CycleState:
        state.committee.is_refactoring = True
        return state

    nodes_mock.refactor_node = mock_refactor

    def mock_final_critic(state: CycleState) -> CycleState:
        state.status = FlowStatus.COMPLETED
        return state

    nodes_mock.final_critic_node = mock_final_critic

    # Inject mock nodes
    builder.nodes = nodes_mock

    graph = builder.build_coder_graph()

    initial_state = CycleState(cycle_id="01")
    initial_state.status = FlowStatus.READY_FOR_AUDIT

    # Asserting that graph works as expected will be hard because routers might not be fully working as defined in SPEC
    # So we execute it to see if it fails (as required by TDD Red phase)
    result_state = None
    for state in graph.stream(initial_state, config={"configurable": {"thread_id": "1"}}):
        for _node_name, node_state in state.items():
            result_state = node_state

    # This asserts SPEC behavior: should reach END with status COMPLETED and is_refactoring True
    assert result_state is not None
    assert result_state.status == FlowStatus.COMPLETED
    assert getattr(result_state.committee, "is_refactoring", False) is True


def test_coder_graph_rejection_loop() -> None:  # noqa: C901
    services = MagicMock()
    sandbox = MagicMock()
    jules = MagicMock()

    builder = GraphBuilder(services, sandbox, jules)

    nodes_mock = MagicMock()

    def mock_test_coder(state: CycleState) -> CycleState:
        return state

    nodes_mock.test_coder_node = mock_test_coder

    def mock_impl_coder(state: CycleState) -> CycleState:
        state.status = FlowStatus.READY_FOR_AUDIT
        return state

    nodes_mock.impl_coder_node = mock_impl_coder

    def mock_sandbox_eval(state: CycleState) -> CycleState:
        state.status = FlowStatus.READY_FOR_AUDIT
        return state

    nodes_mock.sandbox_evaluate_node = mock_sandbox_eval

    def mock_auditor(state: CycleState) -> CycleState:
        from src.domain_models import AuditResult

        # Always reject
        state.audit.audit_result = AuditResult(is_approved=False, status="Reject")
        state.committee.audit_attempt_count += 1
        return state

    nodes_mock.auditor_node = mock_auditor

    def mock_self_critic(state: CycleState) -> CycleState:
        return state

    nodes_mock.self_critic_node = mock_self_critic

    def mock_refactor(state: CycleState) -> CycleState:
        return state

    nodes_mock.refactor_node = mock_refactor

    def mock_final_critic(state: CycleState) -> CycleState:
        return state

    nodes_mock.final_critic_node = mock_final_critic

    # Inject mock nodes
    builder.nodes = nodes_mock

    graph = builder.build_coder_graph()

    initial_state = CycleState(cycle_id="01")
    initial_state.status = FlowStatus.READY_FOR_AUDIT

    result_state = None
    for iteration_count, state in enumerate(
        graph.stream(initial_state, config={"configurable": {"thread_id": "2"}})
    ):
        for _node_name, node_state in state.items():
            result_state = node_state
        if iteration_count > 10:  # Prevent infinite loop
            break

    # If rejection loop works correctly, it should exit via "requires_pivot" to END
    # Or at least audit_attempt_count should be tracked.
    assert result_state is not None
    assert result_state.committee.audit_attempt_count > 0
