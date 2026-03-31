from unittest.mock import AsyncMock

import pytest
from langchain_core.runnables import RunnableConfig

from src.graph import GraphBuilder
from src.sandbox import SandboxRunner
from src.service_container import ServiceContainer
from src.services.jules_client import JulesClient
from src.state import IntegrationState


@pytest.fixture
def mock_sandbox() -> AsyncMock:
    sandbox = AsyncMock(spec=SandboxRunner)
    sandbox.cleanup = AsyncMock()
    return sandbox

@pytest.fixture
def mock_jules() -> AsyncMock:
    jules = AsyncMock(spec=JulesClient)
    jules.create_master_integrator_session.return_value = "test-integrator-session"
    jules.send_message_to_session.return_value = '{"resolved_code": "clean_merged_code"}'
    return jules

def _get_config() -> RunnableConfig:
    return RunnableConfig(configurable={"thread_id": "test_thread"})


@pytest.mark.asyncio
async def test_integration_graph_clean_merge(mock_sandbox: AsyncMock, mock_jules: AsyncMock) -> None:
    """Scenario ID: Integration_Phase_01 - Clean Merge"""
    initial_state = IntegrationState(
        conflict_status=None,
        status=None
    )

    container = ServiceContainer.default()
    builder = GraphBuilder(container, mock_sandbox, mock_jules)

    # Mocking at instance level to avoid patches breaking LangGraph async context
    builder.nodes.git_merge_node = AsyncMock(return_value={"conflict_status": "success"})  # type: ignore[method-assign]
    builder.nodes.global_sandbox_node = AsyncMock(return_value={"status": "pass"})  # type: ignore[method-assign]

    integration_graph = builder.build_integration_graph()

    final_state = await integration_graph.ainvoke(initial_state, _get_config())

    # Assert nodes called
    assert builder.nodes.git_merge_node.call_count == 1
    assert builder.nodes.global_sandbox_node.call_count == 1

    # Final state verification
    assert final_state["conflict_status"] == "success"
    assert final_state["status"] == "pass"


@pytest.mark.asyncio
async def test_integration_graph_conflict_resolution(mock_sandbox: AsyncMock, mock_jules: AsyncMock) -> None:
    """Scenario ID: Integration_Phase_02 - Conflict Resolution via 3-Way Diff"""

    initial_state = IntegrationState(
        conflict_status=None,
        status=None
    )

    container = ServiceContainer.default()
    builder = GraphBuilder(container, mock_sandbox, mock_jules)

    # First call hits a conflict, second succeeds
    builder.nodes.git_merge_node = AsyncMock(side_effect=[{"conflict_status": "conflict_detected"}, {"conflict_status": "success"}])  # type: ignore[method-assign]
    builder.nodes.master_integrator_node = AsyncMock(return_value={"unresolved_conflicts": []})  # type: ignore[method-assign]
    builder.nodes.global_sandbox_node = AsyncMock(return_value={"status": "pass"})  # type: ignore[method-assign]

    integration_graph = builder.build_integration_graph()
    final_state = await integration_graph.ainvoke(initial_state, _get_config())

    assert builder.nodes.git_merge_node.call_count == 2
    assert builder.nodes.master_integrator_node.call_count == 1
    assert builder.nodes.global_sandbox_node.call_count == 1

    assert final_state["conflict_status"] == "success"
    assert final_state["status"] == "pass"


@pytest.mark.asyncio
async def test_integration_graph_semantic_failure_recovery(mock_sandbox: AsyncMock, mock_jules: AsyncMock) -> None:
    """Scenario ID: Integration_Phase_03 - Post-Merge Semantic Failure Recovery"""
    initial_state = IntegrationState(
        conflict_status=None,
        status=None
    )

    container = ServiceContainer.default()
    builder = GraphBuilder(container, mock_sandbox, mock_jules)

    # Git merge succeeds
    builder.nodes.git_merge_node = AsyncMock(return_value={"conflict_status": "success"})  # type: ignore[method-assign]
    # Fails tests initially, passes second time
    builder.nodes.global_sandbox_node = AsyncMock(side_effect=[{"status": "tdd_failed"}, {"status": "pass"}])  # type: ignore[method-assign]
    builder.nodes.integration_fixer_node = AsyncMock(return_value={})  # type: ignore[method-assign]

    integration_graph = builder.build_integration_graph()
    final_state = await integration_graph.ainvoke(initial_state, _get_config())

    assert builder.nodes.git_merge_node.call_count == 1
    assert builder.nodes.global_sandbox_node.call_count == 2
    assert builder.nodes.integration_fixer_node.call_count == 1

    assert final_state["conflict_status"] == "success"
    assert final_state["status"] == "pass"
