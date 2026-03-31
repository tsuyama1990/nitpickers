from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config import settings
from src.domain_models import AuditResult
from src.enums import FlowStatus
from src.graph import GraphBuilder
from src.state import CycleState


@pytest.fixture
def graph_builder() -> GraphBuilder:
    services = MagicMock()
    sandbox = AsyncMock()
    jules = AsyncMock()

    # Needs to match all node attributes in nodes (IGraphNodes)
    nodes_mock = MagicMock()
    nodes_mock.test_coder_node = AsyncMock(
        side_effect=lambda state: {"status": FlowStatus.READY_FOR_AUDIT}
    )
    nodes_mock.impl_coder_node = AsyncMock(
        side_effect=lambda state: {"status": FlowStatus.READY_FOR_AUDIT}
    )
    nodes_mock.sandbox_evaluate_node = AsyncMock(
        side_effect=lambda state: {"status": FlowStatus.READY_FOR_AUDIT}
    )
    nodes_mock.auditor_node = AsyncMock(
        side_effect=lambda state: {"status": FlowStatus.READY_FOR_AUDIT}
    )
    nodes_mock.self_critic_node = AsyncMock(
        side_effect=lambda state: {"status": FlowStatus.READY_FOR_AUDIT}
    )
    nodes_mock.refactor_node = AsyncMock(
        side_effect=lambda state: {
            "committee": {"is_refactoring": True},
            "status": FlowStatus.READY_FOR_AUDIT,
        }
    )
    nodes_mock.final_critic_node = AsyncMock(
        side_effect=lambda state: {"status": FlowStatus.COMPLETED}
    )

    from src.nodes.routers import (
        check_coder_outcome,
        route_auditor,
        route_final_critic,
        route_sandbox_evaluate,
    )

    nodes_mock.check_coder_outcome = check_coder_outcome
    nodes_mock.route_sandbox_evaluate = route_sandbox_evaluate
    nodes_mock.route_auditor = route_auditor
    nodes_mock.route_final_critic = route_final_critic

    gb = GraphBuilder(services, sandbox, jules)
    gb.nodes = nodes_mock
    return gb


@pytest.mark.asyncio
async def test_coder_graph_happy_path(graph_builder: GraphBuilder) -> None:
    graph = graph_builder.build_coder_graph()

    # State needs to successfully traverse test -> impl -> sandbox -> auditor -> next_auditor... -> refactor -> sandbox -> final_critic -> end

    initial_state = {
        "cycle_id": "test_happy_path",
        "status": FlowStatus.READY_FOR_AUDIT,
        "committee": {
            "current_auditor_index": 1,
            "audit_attempt_count": 0,
            "is_refactoring": False,
        },
        "test": {
            "tdd_phase": "green"  # Skipping TDD loop
        },
    }

    # Mock auditor responses sequentially
    def mock_auditor(state: CycleState) -> dict[str, Any]:
        return {"audit": {"audit_result": AuditResult(is_approved=True)}}

    graph_builder.nodes.auditor_node.side_effect = mock_auditor  # type: ignore

    result = await graph.ainvoke(initial_state, config={"configurable": {"thread_id": "1"}})

    assert result["status"] == FlowStatus.COMPLETED
    assert result["committee"]["is_refactoring"] is True
    # If the process successfully visited all 3 auditors, current_auditor_index would increment each time
    assert result["committee"]["current_auditor_index"] == settings.NUM_AUDITORS + 1


@pytest.mark.asyncio
async def test_coder_graph_auditor_rejection_loop(graph_builder: GraphBuilder) -> None:
    graph = graph_builder.build_coder_graph()

    initial_state = {
        "cycle_id": "test_rejection_loop",
        "status": FlowStatus.READY_FOR_AUDIT,
        "committee": {
            "current_auditor_index": 1,
            "audit_attempt_count": 0,
            "is_refactoring": False,
        },
        "test": {"tdd_phase": "green"},
    }

    audit_call_count = 0

    # Mock auditor to reject once, then approve
    def mock_auditor_reject_then_approve(state: CycleState) -> dict[str, Any]:
        nonlocal audit_call_count
        audit_call_count += 1

        # We only want to reject on the very first audit attempt overall
        if audit_call_count == 1:
            return {"audit": {"audit_result": AuditResult(is_approved=False)}}
        return {"audit": {"audit_result": AuditResult(is_approved=True)}}

    graph_builder.nodes.auditor_node.side_effect = mock_auditor_reject_then_approve  # type: ignore

    result = await graph.ainvoke(initial_state, config={"configurable": {"thread_id": "2"}})

    # Ensure it successfully completes eventually
    assert result["status"] == FlowStatus.COMPLETED
    assert result["committee"]["is_refactoring"] is True

    # Ensure attempt count resets to 0 after passing an auditor
    assert result["committee"]["audit_attempt_count"] == 0
    assert result["committee"]["current_auditor_index"] == settings.NUM_AUDITORS + 1
