from unittest.mock import AsyncMock, MagicMock, patch

from typer.testing import CliRunner

from src.cli import app

runner = CliRunner()


def test_run_cycle_command() -> None:
    mock_workflow = MagicMock()
    mock_workflow.run_cycle = AsyncMock()
    with patch("src.cli.WorkflowService", return_value=mock_workflow):
        result = runner.invoke(app, ["run-cycle", "--id", "01"])
        assert result.exit_code == 0
        mock_workflow.run_cycle.assert_awaited_once_with(
            cycle_id="01",
            resume=False,
            auto=False,
            start_iter=1,
            project_session_id=None,
            parallel=False,
        )
