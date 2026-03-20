import contextlib
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from src.domain_models import MultiModalArtifact


# Create a temporary directory fixture to provide actual files for the test
@pytest.fixture
def dummy_files() -> Generator[tuple[Path, Path], None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        screenshot = dir_path / "screenshot.png"
        screenshot.write_text("dummy")
        trace = dir_path / "trace.zip"
        trace.write_text("dummy")
        yield screenshot, trace


def test_multimodal_artifact_valid(dummy_files: tuple[Path, Path]) -> None:
    screenshot, trace = dummy_files
    artifact = MultiModalArtifact(
        test_id="test_foo",
        screenshot_path=str(screenshot),
        trace_path=str(trace),
        console_logs=["error 1"],
        traceback="Exception",
    )
    assert artifact.test_id == "test_foo"
    assert artifact.screenshot_path == str(screenshot)
    assert artifact.trace_path == str(trace)
    assert artifact.console_logs == ["error 1"]
    assert artifact.traceback == "Exception"


def test_multimodal_artifact_missing_screenshot(dummy_files: tuple[Path, Path]) -> None:
    screenshot, trace = dummy_files
    # Delete the screenshot so the validation fails
    screenshot.unlink()

    with pytest.raises(ValidationError, match="Screenshot file not found"):
        MultiModalArtifact(
            test_id="test_foo",
            screenshot_path=str(screenshot),
            trace_path=str(trace),
            console_logs=[],
            traceback="",
        )


def test_multimodal_artifact_missing_trace(dummy_files: tuple[Path, Path]) -> None:
    screenshot, trace = dummy_files
    # Delete the trace so the validation fails
    trace.unlink()

    with pytest.raises(ValidationError, match="Trace file not found"):
        MultiModalArtifact(
            test_id="test_foo",
            screenshot_path=str(screenshot),
            trace_path=str(trace),
            console_logs=[],
            traceback="",
        )


def test_pytest_runtest_makereport_hook_success(monkeypatch: pytest.MonkeyPatch) -> None:
    from tests import conftest

    # Mock the yield_fixture decorator for makereport
    # Since it's a hookwrapper, we need to mock what yield returns
    mock_outcome = MagicMock()

    # In pytest, report objects often don't have all attributes by default
    class MockReport:
        def __init__(self) -> None:
            self.when = "call"
            self.failed = False

    mock_report = MockReport()
    mock_outcome.get_result.return_value = mock_report

    mock_item = MagicMock()

    # Run the generator
    gen = conftest.pytest_runtest_makereport(mock_item, MagicMock())
    next(gen)
    with contextlib.suppress(StopIteration):
        gen.send(mock_outcome)

    # Assert nothing was added to the report since it succeeded
    assert not hasattr(mock_report, "multimodal_artifact")


def test_pytest_runtest_makereport_hook_failure_with_page(
    dummy_files: tuple[Path, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    from tests import conftest

    # We need to simulate the file creation that the hook will attempt.
    # We can mock Path.write_bytes or just let it write to a temp dir by mocking the artifacts dir.
    screenshot, _trace = dummy_files
    artifacts_dir = screenshot.parent

    # Patch the artifacts dir inside conftest
    monkeypatch.setattr("src.config.settings.paths.artifacts_dir", artifacts_dir)

    mock_outcome = MagicMock()
    mock_report = MagicMock()
    mock_report.when = "call"
    mock_report.failed = True  # Test failed!
    mock_report.longreprtext = "Traceback (most recent call last):\n..."
    mock_outcome.get_result.return_value = mock_report

    mock_item = MagicMock()
    mock_item.nodeid = "test_foo.py::test_bar"

    mock_page = MagicMock()
    # Have the screenshot and trace writing actually do nothing since we already created the dummy files
    # but the path generated in the hook will be based on the nodeid. We will intercept the calls.
    mock_page.screenshot.return_value = None
    mock_page.context.tracing.stop.return_value = None

    # Since the paths are generated dynamically by the hook based on test_id,
    # let's pre-create the expected file paths so the MultiModalArtifact validation passes.
    import re

    safe_name = re.sub(r"[^\w\-_\.]", "_", mock_item.nodeid)
    expected_screenshot = artifacts_dir / f"{safe_name}.png"
    expected_trace = artifacts_dir / f"{safe_name}_trace.zip"
    expected_screenshot.write_text("dummy")
    expected_trace.write_text("dummy")

    # Mock fixturenames to include "page"
    mock_item.fixturenames = ["page", "dummy_fixture"]
    mock_item.funcargs = {"page": mock_page}

    # Run the generator
    gen = conftest.pytest_runtest_makereport(mock_item, MagicMock())
    next(gen)
    with contextlib.suppress(StopIteration):
        gen.send(mock_outcome)

    # Verify the hook called the right things
    mock_page.screenshot.assert_called_once_with(
        path=str(expected_screenshot), full_page=True, timeout=5000
    )
    mock_page.context.tracing.stop.assert_called_once_with(path=str(expected_trace))

    # Verify the artifact was attached to the report
    assert hasattr(mock_report, "multimodal_artifact")
    artifact = mock_report.multimodal_artifact
    assert isinstance(artifact, MultiModalArtifact)
    assert artifact.test_id == "test_foo.py::test_bar"
    assert artifact.screenshot_path == str(expected_screenshot)
    assert artifact.trace_path == str(expected_trace)
    assert artifact.traceback == "Traceback (most recent call last):\n..."
