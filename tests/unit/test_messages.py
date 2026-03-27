from unittest.mock import patch

from rich.console import Console
from rich.panel import Panel

from src.messages import RecoveryMessages, SuccessMessages, ensure_api_key


def test_recovery_messages() -> None:
    # Test session_not_found
    result = RecoveryMessages.session_not_found()
    assert "No active session found" in result

    # Test merge_failed
    result = RecoveryMessages.merge_failed("http://pr", "next step cmd")
    assert "http://pr" in result
    assert "next step cmd" in result

    # Test architect_merge_failed
    result = RecoveryMessages.architect_merge_failed("http://pr")
    assert "http://pr" in result
    assert "run-pipeline" in result

    # Test cycle_merge_failed
    result = RecoveryMessages.cycle_merge_failed("http://pr")
    assert "http://pr" in result
    assert "run-pipeline" in result

    # Test branch_not_found
    result = RecoveryMessages.branch_not_found("my-branch")
    assert "my-branch" in result
    assert "Integration branch" in result

    # Test remote_branch_missing
    result = RecoveryMessages.remote_branch_missing("my-branch")
    assert "my-branch" in result
    assert "exists locally but not on remote" in result

    # Test merge_conflict
    result = RecoveryMessages.merge_conflict("src-branch", "tgt-branch", "orig-branch")
    assert "src-branch" in result
    assert "tgt-branch" in result
    assert "orig-branch" in result

def test_success_messages() -> None:
    # Test architect_complete
    result = SuccessMessages.architect_complete("session-123", "int-branch")
    assert "session-123" in result
    assert "int-branch" in result

    # Test cycle_complete with next cycle
    result = SuccessMessages.cycle_complete("cycle-1", "cycle-2")
    assert "cycle-1" in result
    assert "cycle-2" in result

    # Test cycle_complete without next cycle
    result = SuccessMessages.cycle_complete("cycle-1")
    assert "cycle-1" in result
    assert "All cycles have been implemented" in result

    # Test all_cycles_complete
    result = SuccessMessages.all_cycles_complete()
    assert "All Parallel Cycles Complete" in result

    # Test pipeline_complete
    result = SuccessMessages.pipeline_complete()
    assert "Pipeline Verification Complete" in result

    # Test session_finalized
    result = SuccessMessages.session_finalized("http://pr")
    assert "http://pr" in result
    assert "Finalization Complete" in result

def test_show_panel() -> None:
    with patch.object(Console, "print") as mock_print:
        SuccessMessages.show_panel("test message", "test title")
        mock_print.assert_called_once()
        # Ensure it was called with a Panel object
        call_args = mock_print.call_args[0]
        assert len(call_args) > 0
        assert isinstance(call_args[0], Panel)

def test_ensure_api_key_success() -> None:
    with patch("src.messages.check_api_key") as mock_check:
        mock_check.return_value = None
        # Should not raise any exception or exit
        ensure_api_key()
        mock_check.assert_called_once()

def test_ensure_api_key_failure() -> None:
    with (
        patch("src.messages.check_api_key", side_effect=ValueError("Missing API Key")),
        patch("sys.exit") as mock_exit,
        patch.object(Console, "print") as mock_print,
    ):
        ensure_api_key()
        mock_exit.assert_called_once_with(1)
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0]
        assert "Missing API Key" in call_args[0]
