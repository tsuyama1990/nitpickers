from typing import Any
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys

from src.services.workflow import WorkflowService
from src.state_manager import StateManager
from src.domain_models.manifest import ProjectManifest, CycleManifest


@pytest.fixture
def workflow_service() -> Any:
    with patch("src.services.workflow.WorkflowService.verify_environment_and_observability"):
        service = WorkflowService()
        yield service


@pytest.fixture
def dummy_manifest() -> Any:
    return ProjectManifest(
        project_session_id="test_session",
        feature_branch="feature/architecture",
        integration_branch="main",
        cycles=[
            CycleManifest(id="CYCLE01", status="planned"),
            CycleManifest(id="CYCLE02", status="planned"),
        ],
    )


@pytest.mark.asyncio
async def test_run_full_pipeline_phase2_failure(workflow_service: Any, dummy_manifest: Any) -> None:
    """
    Test that if a Coder cycle (Phase 2) fails, the pipeline halts immediately
    and does NOT proceed to Phase 3.
    """
    with patch("src.services.workflow.StateManager.load_manifest", return_value=dummy_manifest):
        with patch.object(workflow_service, "_run_single_cycle") as mock_run_single:
            # Simulate failure in CYCLE02, success in CYCLE01
            async def mock_run(cycle_id: str, **kwargs: Any) -> Any:
                if cycle_id == "CYCLE02":
                    raise RuntimeError("CYCLE02 execution failed")
                return None

            mock_run_single.side_effect = mock_run

            with patch("src.services.workflow.console.print") as mock_print:
                # We expect sys.exit(1) to be called
                with pytest.raises(SystemExit) as exc_info:
                    await workflow_service.run_full_pipeline()

                assert exc_info.value.code == 1

                # Verify failure message is printed
                failure_msgs = [call.args[0] for call in mock_print.call_args_list if isinstance(call.args[0], str) and "Pipeline halted due to Phase 2 failure." in call.args[0]]
                assert len(failure_msgs) > 0

                # Ensure Integration/QA Phase was never reached
                phase3_msgs = [call.args[0] for call in mock_print.call_args_list if isinstance(call.args[0], str) and "Phase 3: Integration Graph" in call.args[0]]
                assert len(phase3_msgs) == 0


@pytest.mark.asyncio
async def test_run_full_pipeline_phase3_failure(workflow_service: Any, dummy_manifest: Any) -> None:
    """
    Test that if Integration Graph (Phase 3) fails, the pipeline halts
    and does NOT proceed to Phase 4.
    """
    with patch("src.services.workflow.StateManager.load_manifest", return_value=dummy_manifest):
        with patch.object(workflow_service, "_run_single_cycle", return_value=None):
            # Mock Phase 3 to return a failed conflict status
            mock_integration_graph = AsyncMock()
            mock_integration_graph.ainvoke.return_value = {"conflict_status": "failed"}

            with patch.object(workflow_service.builder, "build_integration_graph", return_value=mock_integration_graph):
                with patch("src.services.workflow.console.print") as mock_print:
                    # We expect sys.exit(1) to be called
                    with pytest.raises(SystemExit) as exc_info:
                        await workflow_service.run_full_pipeline()

                    assert exc_info.value.code == 1

                    # Verify failure message
                    failure_msgs = [call.args[0] for call in mock_print.call_args_list if isinstance(call.args[0], str) and "Integration Phase Failed: Unresolved conflicts." in call.args[0]]
                    assert len(failure_msgs) > 0

                    # Ensure QA Phase was never reached
                    phase4_msgs = [call.args[0] for call in mock_print.call_args_list if isinstance(call.args[0], str) and "Phase 4: QA/UAT Graph" in call.args[0]]
                    assert len(phase4_msgs) == 0


@pytest.mark.asyncio
async def test_run_full_pipeline_success(workflow_service: Any, dummy_manifest: Any) -> None:
    """
    Test successful execution of all phases.
    """
    # Simulate updated manifest to return branch_name for integration graph
    updated_manifest = dummy_manifest.model_copy()
    updated_manifest.cycles[0].branch_name = "branch_1"
    updated_manifest.cycles[1].branch_name = "branch_2"

    with patch("src.services.workflow.StateManager.load_manifest", side_effect=[dummy_manifest, updated_manifest]):
        with patch.object(workflow_service, "_run_single_cycle", return_value=None):
            # Mock Phase 3 to pass
            mock_integration_graph = AsyncMock()
            mock_integration_graph.ainvoke.return_value = {"conflict_status": "success"}

            # Mock Phase 4 to pass
            mock_qa_graph = AsyncMock()
            mock_qa_graph.ainvoke.return_value = {"status": "completed"}

            with patch.object(workflow_service.builder, "build_integration_graph", return_value=mock_integration_graph):
                with patch.object(workflow_service.builder, "build_qa_graph", return_value=mock_qa_graph):
                    with patch("src.services.workflow.console.print") as mock_print:
                        await workflow_service.run_full_pipeline()

                        # Verify completion message
                        success_msgs = [call.args[0] for call in mock_print.call_args_list if isinstance(call.args[0], str) and "Full Pipeline Execution Completed Successfully." in call.args[0]]
                        assert len(success_msgs) > 0

                        # Ensure all graphs were called
                        assert mock_integration_graph.ainvoke.call_count == 1

                        # Verify the correct state was passed (TDD RED phase check)
                        state_arg = mock_integration_graph.ainvoke.call_args[0][0]
                        assert hasattr(state_arg, "branches_to_merge")
                        assert set(state_arg.branches_to_merge) == {"branch_1", "branch_2"}

                        assert mock_qa_graph.ainvoke.call_count == 1
