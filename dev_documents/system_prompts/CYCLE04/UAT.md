# CYCLE04 User Acceptance Testing

## Test Scenarios

### Scenario 1: Multi-Modal Capture and JSON Manifest Generation
The objective of this scenario is to verify that the system successfully captures a full-page screenshot and explicitly writes a structured `artifact_manifest.json` file when a dynamic Playwright UI test fails. The test simulates a frontend defect by executing a script that attempts to interact with an obscured DOM element. The user initiates the test suite via the CLI. The expected behavior is that the test fails, the custom Pytest hook saves a high-resolution `.png` screenshot to the `artifacts/` directory, and upon session completion, it generates the JSON manifest mapping the test ID to the screenshot path. The system must successfully validate this generated JSON against the `TestReportManifest` Pydantic schema. Executed via Marimo, this scenario provides visual confirmation that the pipeline generates reliable, explicitly mapped visual context, completely eliminating the ambiguity of raw directory scanning.

### Scenario 2: Bypass Capture on Success
This scenario validates the system's robustness by ensuring that the artifact capture and manifest generation mechanisms do not interfere with standard test execution when tests pass successfully. The test simulates a perfectly functioning UI component. The user executes the Playwright test suite. The expected outcome is that the test passes, the Pytest summary reports success, no screenshots are erroneously generated, and either the `artifact_manifest.json` is not created or it is created as a demonstrably empty JSON object (`{}`). This ensures that the system only consumes storage and processing resources when a genuine failure occurs, maintaining the efficiency of the UAT pipeline. This scenario guarantees the mechanical blockade triggers its multi-modal capture sequence accurately and precisely.

## Behavior Definitions
GIVEN a Playwright UI test is executed AND the test encounters an assertion error, WHEN the `pytest_runtest_makereport` hook intercepts the failure, THEN the system must instruct the browser to capture a screenshot, save it to a local directory, AND explicitly write a `TestReportManifest.json` file mapping the test identifier to the absolute paths of the generated visual artifacts.

GIVEN a Playwright UI test executes successfully without exceptions, WHEN the execution completes, THEN the system must bypass the artifact capture sequence entirely AND report a standard passing result, ensuring that the local file system and JSON manifests are not cluttered with unnecessary entries from successful test runs, maintaining a highly precise and performant reporting structure.
