# CYCLE05 SPECIFICATION

## Summary
This cycle implements Phase 2: The Outer Loop (Behavioral Reality Sandbox) focusing entirely on Playwright Multi-Modal Capture. The primary goal is to empower the Stateful Worker to not just run tests, but to physically "see" them fail. To accomplish this, we will integrate the `pytest-playwright` plugin directly into the testing suite and configure Pytest fixtures to automatically capture Multi-Modal Artifacts (full-page PNG screenshots, complete DOM traces as `.txt` or `.html`, and browser console logs) upon any test failure or unhandled UI exception during the dynamic execution phase. This physical evidence is crucial for the Stateless Auditor (OpenRouter Vision LLMs) to correctly diagnose Human-Centered Design compliance and subtle visual bugs that static analyzers completely miss. This cycle ensures these artifacts are saved deterministically and mapped accurately to the `uat_models.py` schema developed in CYCLE01.

## System Architecture
The architecture introduces multi-modal artifact generation within the Outer Loop testing phase. By utilizing Playwright, we step beyond static analysis and verify the dynamic application state inside a simulated browser sandbox (e.g., E2B environments or local headless browsers).

The key architectural addition is the `pytest-playwright` plugin configuration, managed centrally via custom Pytest fixtures and hooks in `tests/conftest.py`. When a UI test assertion fails, Pytest will hook into the active Playwright context via the `pytest_runtest_makereport` hook. This hook will asynchronously pause the teardown, serialize the current DOM, capture a full-page PNG screenshot, and dump the browser's console logs to standard error or a dedicated file.

These artifacts are then physically saved to a predictable output directory (e.g., `dev_documents/test_artifacts/`). The architecture dictates that the file paths must be uniquely deterministic—often utilizing the specific Pytest test name and a timestamp—so that the outer orchestration layer (the `UatUseCase` built in CYCLE06) can systematically parse the directory and bundle the absolute paths into the `UATResult` Pydantic model for ingestion by the Auditor node.

```text
/
├── tests/
│   └── **conftest.py**
└── dev_documents/
    └── **test_artifacts/** (Directory to be created automatically)
```

## Design Architecture
The design architecture requires configuring advanced Pytest hooks and Playwright fixture dependencies.

When the `pytest_runtest_makereport` hook fires, it inspects the test report object. If the `report.when == 'call'` and the `report.failed` flag is true, the hook must attempt to access the Playwright `page` fixture bound to the currently failing test item. If the `page` fixture exists (indicating a UI test rather than a standard unit test), the hook asynchronously invokes `page.screenshot()` and `page.content()`.

The output directory `dev_documents/test_artifacts/` must be dynamically created if it does not exist using `pathlib.Path.mkdir(parents=True, exist_ok=True)`. The generated screenshot file must be named something like `{item.name}_screenshot.png` and the DOM trace `{item.name}_dom.txt`. A critical design constraint is exception handling within the hook itself: if the browser context crashed before capture, the hook must fail gracefully without hanging the entire test suite, simply logging that the artifact capture failed.

## Implementation Approach
The implementation approach involves injecting the `pytest-playwright` configuration logic securely into `tests/conftest.py`.

**Step 1:** Add the `pytest-playwright` plugin dependency (already done in `pyproject.toml` globally, but ensure it is importable). In `tests/conftest.py`, define a `pytest_runtest_makereport` hook.

**Step 2:** Within the hook, use `@pytest.hookimpl(tryfirst=True, hookwrapper=True)` to intercept the test execution. Yield to let the test run, then inspect the result (`outcome = yield`, `report = outcome.get_result()`).

**Step 3:** If `report.when == 'call'` and `report.failed`: identify if a `page` fixture was active on the `item` (e.g., `page = item.funcargs.get('page')`).

**Step 4:** If `page` exists, immediately capture the screenshot: `page.screenshot(path=str(artifact_dir / f"{item.name}.png"), full_page=True)`. Capture the DOM: `dom_content = page.content()`, then write `dom_content` to `artifact_dir / f"{item.name}_dom.txt"`. Wrap these Playwright calls in a broad `try/except Exception as e` block to ensure that if the browser process is dead, the test suite still exits cleanly, printing the capture error to `stderr`.

## Test Strategy

### Unit Testing Approach
The unit tests will mock the Pytest report and the Playwright `page` objects to verify the isolation and correctness of the capture logic. We will use `unittest.mock.MagicMock` to simulate a Pytest `item` with a mock `page` fixture. We will invoke our custom `pytest_runtest_makereport` hook directly with a mocked failing report object. We will assert that the hook correctly identifies the failure, calls the `mkdir` function to ensure the artifact directory exists, and calls `page.screenshot` and `page.content` with the properly formatted deterministic file paths. We will also test the exception handling by configuring the mock `page.screenshot` to throw a `TimeoutError`, ensuring the hook catches it and does not propagate the error to crash Pytest.

### Integration Testing Approach
The integration testing approach will execute a genuine Pytest session in a subprocess using `pytest.main()`. We will configure a dummy UI test designed to fail intentionally (e.g., using a headless Playwright context to navigate to a local mock HTML file and asserting on a non-existent CSS selector). We will run the suite and verify that the test fails correctly. More importantly, we will assert that the `dev_documents/test_artifacts/` directory now contains the generated `.png` and `.txt` DOM artifacts, and that the screenshot is not a zero-byte file, proving the multi-modal capture pipeline is operational.
