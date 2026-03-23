from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domain_models.manifest import CycleManifest
from src.services.workflow import WorkflowService


@pytest.fixture
def mock_manifest() -> MagicMock:
    manifest = MagicMock()
    manifest.cycles = [
        CycleManifest(id="01", status="planned"),
        CycleManifest(id="02", status="planned"),
    ]
    manifest.feature_branch = "integration"
    return manifest


@pytest.fixture
def workflow_service() -> WorkflowService:
    service = WorkflowService()
    service.verify_environment_and_observability = MagicMock()  # type: ignore[method-assign]
    return service


@pytest.mark.asyncio
@patch("src.services.workflow.StateManager")
@patch("src.services.workflow.AsyncDispatcher")
async def test_run_full_pipeline_success(
    mock_dispatcher_class: MagicMock,
    mock_state_manager_class: MagicMock,
    workflow_service: WorkflowService,
    mock_manifest: MagicMock,
) -> None:
    mock_mgr = mock_state_manager_class.return_value
    mock_mgr.load_manifest.return_value = mock_manifest

    mock_dispatcher = mock_dispatcher_class.return_value
    mock_dispatcher.resolve_dag.return_value = [mock_manifest.cycles]

    from collections.abc import Coroutine
    from typing import Any

    async def run_semaphore_mock(coro: Coroutine[Any, Any, Any]) -> Any:
        return await coro

    mock_dispatcher.run_with_semaphore = run_semaphore_mock

    workflow_service._run_single_cycle = AsyncMock()  # type: ignore[method-assign]

    mock_integration_graph = MagicMock()
    mock_integration_graph.ainvoke = AsyncMock(return_value={"conflict_status": "success"})

    mock_qa_graph = MagicMock()
    mock_qa_graph.ainvoke = AsyncMock(return_value={"status": "completed"})

    workflow_service.builder.build_integration_graph = MagicMock(  # type: ignore[method-assign]
        return_value=mock_integration_graph
    )
    workflow_service.builder.build_qa_graph = MagicMock(return_value=mock_qa_graph)  # type: ignore[method-assign]

    await workflow_service.run_full_pipeline(project_session_id="test_session")

    assert workflow_service._run_single_cycle.call_count == 2
    mock_integration_graph.ainvoke.assert_called_once()
    mock_qa_graph.ainvoke.assert_called_once()


@pytest.mark.asyncio
@patch("src.services.workflow.StateManager")
@patch("src.services.workflow.AsyncDispatcher")
async def test_run_full_pipeline_fail_fast_on_coder(
    mock_dispatcher_class: MagicMock,
    mock_state_manager_class: MagicMock,
    workflow_service: WorkflowService,
    mock_manifest: MagicMock,
) -> None:
    mock_mgr = mock_state_manager_class.return_value
    mock_mgr.load_manifest.return_value = mock_manifest

    mock_dispatcher = mock_dispatcher_class.return_value
    mock_dispatcher.resolve_dag.return_value = [mock_manifest.cycles]

    from collections.abc import Coroutine
    from typing import Any

    async def run_semaphore_mock(coro: Coroutine[Any, Any, Any]) -> Any:
        return await coro

    mock_dispatcher.run_with_semaphore = run_semaphore_mock

    from typing import Any

    async def single_cycle_mock(cycle_id: str, **kwargs: Any) -> None:
        if cycle_id == "02":
            msg = "Intentional coder failure"
            raise ValueError(msg)

    workflow_service._run_single_cycle = AsyncMock(side_effect=single_cycle_mock)  # type: ignore[method-assign]

    mock_integration_graph = MagicMock()
    mock_qa_graph = MagicMock()
    workflow_service.builder.build_integration_graph = MagicMock(  # type: ignore[method-assign]
        return_value=mock_integration_graph
    )
    workflow_service.builder.build_qa_graph = MagicMock(return_value=mock_qa_graph)  # type: ignore[method-assign]

    with pytest.raises(SystemExit) as exit_info:
        await workflow_service.run_full_pipeline(project_session_id="test_session")

    assert exit_info.value.code == 1
    assert workflow_service._run_single_cycle.call_count == 2
    mock_integration_graph.ainvoke.assert_not_called()
    mock_qa_graph.ainvoke.assert_not_called()


@pytest.mark.asyncio
@patch("src.services.workflow.StateManager")
@patch("src.services.workflow.AsyncDispatcher")
async def test_run_full_pipeline_fail_on_integration(
    mock_dispatcher_class: MagicMock,
    mock_state_manager_class: MagicMock,
    workflow_service: WorkflowService,
    mock_manifest: MagicMock,
) -> None:
    mock_mgr = mock_state_manager_class.return_value
    mock_mgr.load_manifest.return_value = mock_manifest

    mock_dispatcher = mock_dispatcher_class.return_value
    mock_dispatcher.resolve_dag.return_value = [mock_manifest.cycles]

    from collections.abc import Coroutine
    from typing import Any

    async def run_semaphore_mock(coro: Coroutine[Any, Any, Any]) -> Any:
        return await coro

    mock_dispatcher.run_with_semaphore = run_semaphore_mock

    workflow_service._run_single_cycle = AsyncMock()  # type: ignore[method-assign]

    mock_integration_graph = MagicMock()
    mock_integration_graph.ainvoke = AsyncMock(return_value={"conflict_status": "failed"})

    mock_qa_graph = MagicMock()

    workflow_service.builder.build_integration_graph = MagicMock(  # type: ignore[method-assign]
        return_value=mock_integration_graph
    )
    workflow_service.builder.build_qa_graph = MagicMock(return_value=mock_qa_graph)  # type: ignore[method-assign]

    with pytest.raises(SystemExit) as exit_info:
        await workflow_service.run_full_pipeline(project_session_id="test_session")

    assert exit_info.value.code == 1
    assert workflow_service._run_single_cycle.call_count == 2
    mock_integration_graph.ainvoke.assert_called_once()
    mock_qa_graph.ainvoke.assert_not_called()
