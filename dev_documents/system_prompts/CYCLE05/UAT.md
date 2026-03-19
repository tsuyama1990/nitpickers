# CYCLE05 UAT

## Test Scenarios

### Scenario ID: SCENARIO-05-1
**Priority**: High
This scenario verifies the core Multi-Modal Capture mechanism. The user will trigger a Playwright UI test that is explicitly programmed to fail (e.g., asserting that an element containing the text "Welcome" exists on a blank page). They will run the test suite and verify that the `pytest_runtest_makereport` hook correctly intercepts the failure, automatically generating a full-page `.png` screenshot and a `.txt` DOM trace, saving them securely to the designated artifacts directory.

### Scenario ID: SCENARIO-05-2
**Priority**: Medium
This scenario tests the gracefulness of the capture hook under adverse conditions. The user will execute a Playwright test that simulates a severe browser crash or context closure before the assertion fails. They will verify that the custom Pytest hook attempts the capture, catches the resulting Playwright `Error` or `TimeoutError` without crashing the entire test suite, and allows Pytest to exit with a standard non-zero code, reporting the missing artifacts gracefully to stderr.

### Scenario ID: SCENARIO-05-3
**Priority**: High
This scenario tests that successful tests do not clutter the artifact directory. The user will execute a Playwright UI test that passes all assertions perfectly. They will verify that the test completes successfully and that the `pytest_runtest_makereport` hook correctly ignores the passing state, resulting in absolutely no new `.png` or `.txt` files being written to the `test_artifacts` directory.

## Behavior Definitions

GIVEN a Playwright UI test is configured to fail an assertion
WHEN the Pytest suite is executed (`uv run pytest`)
THEN the test runner identifies the failure during the teardown hook
AND it automatically calls the Playwright page methods to capture a screenshot and DOM trace
AND saves these artifacts to the `dev_documents/test_artifacts/` directory using the test name as the file prefix.

GIVEN a Playwright UI test that crashes the browser context (e.g., navigating to an invalid local port and forcing a hard timeout)
WHEN the Pytest suite evaluates the failure
THEN the custom capture hook safely catches the Playwright `TargetClosedError` or `TimeoutError`
AND logs the capture failure to standard error without halting the test suite's execution loop.

GIVEN a Playwright UI test that passes all assertions flawlessly
WHEN the Pytest suite executes the test
THEN the test report indicates success
AND the custom capture hook bypasses the artifact generation sequence entirely, leaving the `test_artifacts` directory unmodified.
