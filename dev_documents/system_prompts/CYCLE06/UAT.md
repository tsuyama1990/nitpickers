# CYCLE06 UAT

## Test Scenarios

### Scenario ID: SCENARIO-06-1
**Priority**: High
This scenario tests the fundamental dynamic execution mechanism under failure conditions. The user observes that the UAT pipeline now genuinely executes tests dynamically, halting the agent workflow upon detecting an error rather than assuming success. The user triggers the workflow with a known failing test and verifies that the system does not advance to pull request creation, but instead correctly captures the failure state.

### Scenario ID: SCENARIO-06-2
**Priority**: High
This scenario tests the dynamic execution mechanism under successful conditions. The user provides a perfectly passing test suite and executes the workflow. They verify that the `UatUseCase` correctly identifies the zero exit code, bypasses the artifact traversal logic, and seamlessly routes the state vector forward to the PR creation phase, validating the "happy path" of the zero-trust pipeline.

### Scenario ID: SCENARIO-06-3
**Priority**: Medium
This scenario tests edge cases of dynamic execution, specifically the artifact resolution logic. The user simulates a UAT failure where the Playwright browser crashed instantaneously, failing to write the `.png` screenshot to the disk. They execute the workflow and verify that the `UatUseCase` handles the missing file gracefully, populating the `UATResult` with the error trace but `None` for the artifact paths, preventing the orchestration layer from crashing due to `FileNotFound` exceptions.

## Behavior Definitions

GIVEN a Pytest script that is explicitly designed to fail an assertion
WHEN the dynamic UAT Use Case executes the test suite
THEN the execution naturally captures the non-zero exit code and failure state
AND it successfully bundles the generated multi-modal artifact paths
AND the workflow router explicitly prevents the state from advancing to the PR creation phase.

GIVEN a Pytest script that passes all assertions flawlessly
WHEN the UAT Use Case executes the suite via the ProcessRunner
THEN the system captures an exit code of zero
AND the state dictionary is updated to reflect a successful UAT phase
AND the workflow router linearly advances the process to finalize the codebase.

GIVEN a failing test execution where the expected visual artifacts are completely missing from the filesystem
WHEN the UAT Use Case attempts to locate the screenshots
THEN the service gracefully handles the absence of the files
AND populates the state dictionary with the textual error trace without crashing the agent loop.
