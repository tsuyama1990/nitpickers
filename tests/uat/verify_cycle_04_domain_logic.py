import marimo

__generated_with = "0.11.0"
app = marimo.App(width="medium")


@app.cell
def _() -> tuple:
    from pathlib import Path

    import pytest

    # Scenario 1: Multi-Modal Capture on Failure
    # We create a temporary pytest file that fails purposefully.

    test_file_content = "import pytest\n\ndef test_failure(page):\n    page.goto('data:text/html,<html><body><h1>Hello World</h1></body></html>')\n    page.click('button#non-existent', timeout=100)\n"

    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        test_file = tmp_path / "test_ui_failure.py"
        test_file.write_text(test_file_content)

        # We need to explicitly point to the conftest.py otherwise it won't load the hook
        conftest_path = Path.cwd() / "tests" / "conftest.py"

        # Run pytest programmatically on this file, telling it to use chromium
        # We need to explicitly enable playwright trace capturing
        result = pytest.main(["-v", str(test_file), "--browser=chromium", "--tracing=on", f"-c={Path.cwd() / 'pyproject.toml'}", f"--confcutdir={Path.cwd()}", f"--rootdir={Path.cwd()}", str(conftest_path)])

        # result should be TESTS_FAILED
        # Sometimes due to the unrecognized argument it could return USAGE_ERROR
        # But wait, why unrecognized --browser=chromium? The playwright plugin must be loaded.
        # Let's ensure pytest-playwright is installed and loaded
        assert result == pytest.ExitCode.TESTS_FAILED, f"The test should have failed. Exit code was: {result}"

        # Verify artifacts were generated
        artifacts_dir = Path("dev_documents/artifacts")
        assert artifacts_dir.exists(), "Artifacts directory should have been created."

        # The node id will be something like `/tmp/tmp123/test_ui_failure.py::test_failure`
        # Because the hook does item.nodeid, it will be relative to the pytest invocation dir.
        # But we pass the absolute path to pytest.main. Let's list the dir and find the files instead
        # to make it robust.

        screenshots = list(artifacts_dir.glob("*.png"))
        traces = list(artifacts_dir.glob("*_trace.zip"))

        assert len(screenshots) > 0, "At least one screenshot should exist."
        assert len(traces) > 0, "At least one trace should exist."

    return (artifacts_dir, screenshots, traces, result, test_file_content, tmp_path)


@app.cell
def _() -> None:
    return


if __name__ == "__main__":
    app.run()
