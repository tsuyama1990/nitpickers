# UAT: Cycle 04 - Sandbox UAT Verification Setup

## Test Scenarios

### Scenario ID: UAT-C04-001 - Sandbox Failure Extraction Loop
**Priority**: High
**Description**: This scenario proves the Zero-Trust Validation mechanism physically functions. We will push a Python file containing an intentional logical error (e.g., returning the wrong value type) alongside its corresponding `pytest` file into the E2B sandbox. The test must verify that the test executes remotely, fails correctly, and that the orchestrator captures the precise `pytest` traceback. This traceback must be accurately routed back to the Jules Coder session for an evidence-based refactoring loop, demonstrating that the AI is no longer relying on hallucinations but on physical execution data.

### Scenario ID: UAT-C04-002 - Sandbox Successful Execution
**Priority**: Medium
**Description**: This scenario verifies the successful path. We will provide a completely correct Python file and test file. The system will sync these to the E2B sandbox. The orchestrator must execute `pytest`, receive a `0` exit code, correctly parse the success metrics (including code coverage if available), update the LangGraph state to reflect the successful execution artifact, and allow the workflow to proceed to the Auditor Review phase. This test proves that the remote execution bridge is stable and does not generate false negatives.

## Behavior Definitions

```gherkin
Feature: Remote Sandbox Test Verification
  As an AI Orchestrator
  I want to securely execute tests in an isolated sandbox environment
  So that I have deterministic proof of code correctness before merging

  Scenario: Extracting an execution traceback from a failed remote test
    Given the Coder session has generated source code and a test script
    And the source code contains a deliberate logical flaw
    When the workflow transitions to the Sandbox UAT node
    Then the system must sync the files to the remote E2B container
    And it must execute the test command
    And the remote execution must return a non-zero exit code
    And the orchestrator must extract the specific test failure traceback
    And the traceback must be formatted into a prompt and sent back to the Coder session

  Scenario: Processing a successful remote test execution
    Given the Coder session has generated flawless source code and tests
    When the workflow transitions to the Sandbox UAT node
    Then the system must execute the test command remotely
    And the remote execution must return an exit code of 0
    And the orchestrator must record the success artifact in the system state
    And the workflow must proceed to the Auditor Review node
```
