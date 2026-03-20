# CYCLE04 User Acceptance Testing

## Test Scenarios

### Scenario 1: Multi-Modal Capture on Failure
The objective of this scenario is to verify that the system successfully captures a full-page screenshot and DOM trace when a dynamic Playwright UI test fails. The test will simulate a frontend defect by executing a test script that attempts to interact with a button that is explicitly obscured or missing from the DOM. The user will initiate the test suite via the CLI. The expected behavior is that the Playwright test fails, and immediately upon failure, the custom Pytest hook intercepts the event and saves a high-resolution `.png` screenshot to the designated `artifacts/` directory. The system must also successfully validate the generated file paths against the `MultiModalArtifact` Pydantic schema. This scenario, executed interactively via Marimo, provides visual confirmation that the pipeline can reliably generate the crucial visual context required by the Auditor agent, ensuring that frontend failures are never "Black Boxes" but rather actionable datasets.

### Scenario 2: Bypass Capture on Success
This scenario validates the system's robustness by ensuring that the artifact capture mechanism does not interfere with standard test execution when tests pass successfully. The test simulates a perfectly functioning UI component. The user executes the Playwright test suite. The expected outcome is that the test passes, the Pytest summary reports success, and crucially, no screenshots or trace files are erroneously generated or saved to the `artifacts/` directory. This ensures that the system only consumes storage and processing resources when a genuine failure occurs, maintaining the efficiency and performance of the UAT pipeline during successful development cycles. This Marimo scenario guarantees that the mechanical blockade only triggers its multi-modal capture sequence when absolutely necessary, preventing log bloat.

## Behavior Definitions
GIVEN a Playwright UI test is executed AND the test encounters an assertion error or timeout, WHEN the `pytest_runtest_makereport` hook intercepts the failure, THEN the system must instruct the active browser context to capture a full-page screenshot and DOM state, save these artifacts to a standardized local directory, AND validate the resulting file paths using the strict Pydantic schema.

GIVEN a Playwright UI test executes successfully without raising any exceptions, WHEN the execution completes, THEN the system must bypass the artifact capture sequence entirely AND report a standard passing result, ensuring that the local file system is not cluttered with unnecessary visual artifacts from successful test runs, maintaining a clean and performant execution environment for the automated pipeline.
