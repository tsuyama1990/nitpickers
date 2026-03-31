from typing import Any
import pytest
from unittest.mock import AsyncMock, patch
from typer.testing import CliRunner

from src.cli import app
from src.domain_models.manifest import ProjectManifest, CycleManifest

runner = CliRunner()

@pytest.fixture
def dummy_manifest() -> Any:
    return ProjectManifest(
        project_session_id="integration_session",
        feature_branch="feature/test-orchestration",
        integration_branch="main",
        cycles=[
            CycleManifest(id="CYCLE01", status="planned"),
            CycleManifest(id="CYCLE02", status="planned"),
        ],
    )


def test_cli_run_pipeline_success(dummy_manifest: Any) -> None:
    """
    Test successful execution of the CLI command run-pipeline
    """
    # Create updated manifest
    updated_manifest = dummy_manifest.model_copy()
    updated_manifest.cycles[0].branch_name = "branch_1"
    updated_manifest.cycles[1].branch_name = "branch_2"

    with patch("src.services.workflow.WorkflowService.verify_environment_and_observability"):
        with patch("src.services.workflow.StateManager.load_manifest", side_effect=[dummy_manifest, updated_manifest]):
            with patch("src.services.workflow.WorkflowService._run_single_cycle", new_callable=AsyncMock) as mock_run_single:
                mock_run_single.return_value = None

                # Mock Integration Graph
                mock_integration_graph = AsyncMock()
                mock_integration_graph.ainvoke.return_value = {"conflict_status": "success"}

                # Mock QA Graph
                mock_qa_graph = AsyncMock()
                mock_qa_graph.ainvoke.return_value = {"status": "completed"}

                with patch("src.services.workflow.GraphBuilder.build_integration_graph", return_value=mock_integration_graph):
                    with patch("src.services.workflow.GraphBuilder.build_qa_graph", return_value=mock_qa_graph):

                        result = runner.invoke(app, ["run-pipeline", "--parallel"])

                        assert result.exit_code == 0
                        assert "Starting Full Pipeline Orchestration" in result.stdout
                        assert "Phase 2: Parallel Coder Graph" in result.stdout
                        assert "Phase 3: Integration Graph" in result.stdout
                        assert "Phase 4: QA/UAT Graph" in result.stdout
                        assert "Full Pipeline Execution Completed Successfully" in result.stdout

                        # Verify correct integration state (TDD RED phase check)
                        state_arg = mock_integration_graph.ainvoke.call_args[0][0]
                        assert set(state_arg.branches_to_merge) == {"branch_1", "branch_2"}



def test_cli_run_pipeline_failure(dummy_manifest: Any) -> None:
    """
    Test fail fast behavior from CLI command run-pipeline
    """
    with patch("src.services.workflow.WorkflowService.verify_environment_and_observability"):
        with patch("src.services.workflow.StateManager.load_manifest", return_value=dummy_manifest):
            with patch("src.services.workflow.WorkflowService._run_single_cycle", new_callable=AsyncMock) as mock_run_single:

                # Simulate failure in CYCLE02
                async def mock_run(cycle_id: str, **kwargs: Any) -> Any:
                    if cycle_id == "CYCLE02":
                        raise RuntimeError("Mock failure in CYCLE02")
                    return None

                mock_run_single.side_effect = mock_run

                result = runner.invoke(app, ["run-pipeline", "--parallel"])

                assert result.exit_code != 0
                assert "Starting Full Pipeline Orchestration" in result.stdout
                assert "Phase 2: Parallel Coder Graph" in result.stdout
                assert "Pipeline halted due to Phase 2 failure." in result.stdout
                # Ensure no further phases ran
                assert "Phase 3: Integration Graph" not in result.stdout
                assert "Phase 4: QA/UAT Graph" not in result.stdout
