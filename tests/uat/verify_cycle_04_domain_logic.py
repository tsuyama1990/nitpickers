import marimo

__generated_with = "0.11.0"
app = marimo.App(width="medium")


@app.cell
def _() -> tuple:
    from dataclasses import dataclass
    from pathlib import Path

    import pytest

    @dataclass
    class UATCaptureResult:
        artifacts_dir: Path
        screenshots: list[Path]
        traces: list[Path]
        exit_code: int
        tmp_path: Path

    TEST_FAILURE_CONTENT = "import pytest\n\ndef test_failure(page):\n    page.goto('data:text/html,<html><body><h1>Hello World</h1></body></html>')\n    page.click('button#non-existent', timeout=100)\n"
    EXPECTED_EXIT_CODE = pytest.ExitCode.TESTS_FAILED

    return UATCaptureResult, TEST_FAILURE_CONTENT, EXPECTED_EXIT_CODE


@app.cell
def _(UATCaptureResult, TEST_FAILURE_CONTENT, EXPECTED_EXIT_CODE) -> tuple:
    import tempfile
    from pathlib import Path as _Path

    import pytest as _pytest

    from src.config import settings
    # Scenario 1: Multi-Modal Capture on Failure
    # We create a temporary pytest file that fails purposefully.

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = _Path(tmpdir)
        test_file = tmp_path / "test_ui_failure.py"
        test_file.write_text(TEST_FAILURE_CONTENT)

        # We need to explicitly point to the conftest.py otherwise it won't load the hook
        conftest_path = _Path.cwd() / "tests" / "conftest.py"

        # Run pytest programmatically on this file, telling it to use chromium
        # We need to explicitly enable playwright trace capturing
        PYTEST_ARGS = [
            "-v",
            str(test_file),
            "--browser=chromium",
            "--tracing=on",
            f"-c={_Path.cwd() / 'pyproject.toml'}",
            f"--confcutdir={_Path.cwd()}",
            f"--rootdir={_Path.cwd()}",
            str(conftest_path),
        ]
        result = _pytest.main(PYTEST_ARGS)

        assert result == EXPECTED_EXIT_CODE, f"The test should have failed. Exit code was: {result}"

        # Verify artifacts were generated
        artifacts_dir = settings.paths.artifacts_dir
        assert artifacts_dir.exists(), "Artifacts directory should have been created."

        # The node id will be something like `/tmp/tmp123/test_ui_failure.py::test_failure`
        # Because the hook does item.nodeid, it will be relative to the pytest invocation dir.
        # But we pass the absolute path to pytest.main. Let's list the dir and find the files instead
        # to make it robust.

        screenshots = list(artifacts_dir.glob("*.png"))
        traces = list(artifacts_dir.glob("*_trace.zip"))

        assert len(screenshots) > 0, "At least one screenshot should exist."
        assert len(traces) > 0, "At least one trace should exist."

    res = UATCaptureResult(
        artifacts_dir=artifacts_dir,
        screenshots=screenshots,
        traces=traces,
        exit_code=int(result),
        tmp_path=tmp_path,
    )
    return (res,)


if __name__ == "__main__":
    app.run()
