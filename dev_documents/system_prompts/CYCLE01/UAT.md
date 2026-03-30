# CYCLE01 UAT: State Management and Coder Graph Refactoring Verification

## Test Scenarios

### SCENARIO-01: Seamless Serial Auditing Progression and Post-Refactor Routing
- **Priority**: High
- **Description**: This scenario is the primary happy-path validation for the newly refactored Coder Graph (Phase 2). The objective is to absolutely verify that the system correctly forces the generated code through three sequential, independent auditing steps before it ever considers the implementation complete. Furthermore, it must prove that once these three auditors issue an approval, the system transitions into the refactoring state, and subsequently routes back through the sandbox to the final critic, entirely bypassing the auditors on the second pass. If the system fails to increment the `current_auditor_index` correctly, or if it routes back to `auditor_node` after the refactor instead of `final_critic_node`, the architectural constraints are broken.
- **Verification Method**: This test must be executed deterministically using the `tutorials/UAT_AND_TUTORIAL.py` Marimo notebook running strictly in Mock Mode. This ensures no real API keys are consumed.
  1. Initialize a mock `CycleState` representing a simple feature addition.
  2. Trigger the compiled `_create_coder_graph`.
  3. The mock `auditor_node` must be programmed to return an "Approve" result exactly three times in a row.
  4. Assert that after the first pass, `state.committee.current_auditor_index` equals 2.
  5. Assert that after the second pass, the index equals 3.
  6. Assert that after the third pass, the routing edge `"pass_all"` is triggered, directing flow to `refactor_node`.
  7. Assert that `refactor_node` successfully mutates `state.committee.is_refactoring` to `True`.
  8. Finally, assert that the subsequent `sandbox_evaluate` success path evaluates `is_refactoring == True` and routes perfectly to `final_critic_node`, culminating in the `END` state.

### SCENARIO-02: Graceful Fallback on Auditor Rejection Limits
- **Priority**: High
- **Description**: This scenario is the critical safety net validation. The objective is to verify that the Coder Graph contains an unbreakable mathematical limit on how many times an auditor can reject a piece of code. Without this limit, the system is vulnerable to infinite ping-pong loops where the coder repeatedly fails to satisfy the auditor's strict demands, burning continuous compute and API resources. This test ensures that the `audit_attempt_count` increments correctly on rejection, and that exceeding a predefined maximum forces the system out of the loop and back to the implementation stage (or a hard fail state) for a fresh approach.
- **Verification Method**: This test must also be executed using the `tutorials/UAT_AND_TUTORIAL.py` Marimo notebook in Mock Mode to maintain deterministic control over the auditor's responses.
  1. Initialize a mock `CycleState`.
  2. Trigger the compiled `_create_coder_graph`.
  3. The mock `auditor_node` must be rigidly programmed to return a "Reject" result continuously.
  4. Assert that after the first rejection, the `state.committee.audit_attempt_count` increments exactly to 1, and the system loops back to the `coder_session`.
  5. Assert that after the second rejection, the count increments to 2.
  6. Assert that when the count reaches the configured maximum threshold (e.g., `attempt_count > 2`), the `route_auditor` logic fundamentally changes its behavior. Instead of returning `"reject"` to simply loop back for a minor fix, it must trigger a major fallback signal (such as routing to a pivot node or failing the cycle entirely) to break the infinite loop paradigm securely.

## Behavior Definitions

### Gherkin Definitions

The following behavior definitions utilize Gherkin syntax to explicitly mandate the expected input conditions and output routing logic for the newly established Coder Graph components. These definitions act as strict contracts for the unit and integration testing suites.

**Feature: Serial Auditing Progression and Refactor Routing**
```gherkin
  Scenario: Passing all three serial auditors successfully triggers the refactoring node
    Given the Coder Graph has completed the initial feature implementation
    And the generated code successfully passes the initial mechanical sandbox evaluation
    And the state property `current_auditor_index` is initialized to 1
    And the state property `is_refactoring` is initialized to False
    When Auditor 1 evaluates the code and issues an explicit Approval
    Then the state property `current_auditor_index` should increment exactly to 2
    And the system should route back to the auditor_node for the second review

    When Auditor 2 evaluates the code and issues an explicit Approval
    Then the state property `current_auditor_index` should increment exactly to 3
    And the system should route back to the auditor_node for the final review

    When Auditor 3 evaluates the code and issues an explicit Approval
    Then the routing logic should recognize the index maximum has been reached
    And the system should trigger the `pass_all` conditional edge
    And the system should route directly to the `refactor_node`
    And the `refactor_node` must mutate the state property `is_refactoring` to True before concluding
```

**Feature: Auditor Rejection Limit and Infinite Loop Prevention**
```gherkin
  Scenario: The system safely breaks out of an auditing loop after repeated rejections
    Given the code is currently being reviewed by Auditor 1 within the Coder Graph
    And the state property `audit_attempt_count` is currently 0
    When Auditor 1 evaluates the code and issues a Rejection with feedback
    Then the state property `audit_attempt_count` should increment to exactly 1
    And the system should route the feedback back to the `coder_session` for minor remediation

    When the Coder resubmits the code and Auditor 1 issues a second consecutive Rejection
    Then the state property `audit_attempt_count` should increment to exactly 2

    When the Coder resubmits the code and Auditor 1 issues a third consecutive Rejection
    Then the routing logic should recognize that `audit_attempt_count` has exceeded the safe threshold
    And the system must refuse to route back to the standard `coder_session`
    And the system must trigger a major fallback or failure edge to permanently break the infinite retry loop
```

**Feature: Post-Refactoring Direct Route to Final Critic**
```gherkin
  Scenario: A successfully refactored codebase entirely bypasses the serial auditors
    Given the system has successfully completed the `refactor_node` execution
    And the state property `is_refactoring` has been permanently set to True
    When the newly refactored code is sent back through the mechanical `sandbox_evaluate` node
    And the refactored code successfully passes all static linters and dynamic unit tests
    Then the router `route_sandbox_evaluate` must evaluate the `is_refactoring` flag
    And the router must explicitly bypass the `auditor_node` pathway
    And the router must route the state directly to the `final_critic_node` for ultimate verification before the cycle concludes
```