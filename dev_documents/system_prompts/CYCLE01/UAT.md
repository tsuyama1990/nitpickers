# CYCLE01 UAT Plan

## Test Scenarios

### ID: UAT-C01-001 (Priority: High)
- **Title**: Verify `CycleState` Initialization and Pydantic Validation Constraints
- **Description**: Ensure that the newly added fields (`is_refactoring`, `current_auditor_index`, `audit_attempt_count`) are correctly initialized and their invariants (e.g., `current_auditor_index` >= 1) are strictly enforced by Pydantic.
- **Why**: This proves the domain models are robust and prevents the orchestrator from entering invalid states or infinite loops during the serial audit phase.

### ID: UAT-C01-002 (Priority: High)
- **Title**: Verify `route_sandbox_evaluate` Conditional Branching
- **Description**: Ensure the router function correctly directs the flow to "auditor" when `is_refactoring` is False, and to "final_critic" when `is_refactoring` is True, given a passing test status.
- **Why**: This verifies the foundational logic that separates the implementation phase from the post-audit refactoring phase.

### ID: UAT-C01-003 (Priority: Medium)
- **Title**: Verify `route_auditor` Loop Progression and Fallback
- **Description**: Ensure the router increments the auditor index on approval, loops back on rejection, and triggers "pass_all" when the maximum auditor count is reached. It must also handle maximum attempt counts (e.g., fallback after 2 rejections).
- **Why**: This proves the serial audit loop works as intended without deadlocking the graph.

### ID: UAT-C01-004 (Priority: High)
- **Title**: Verify `build_conflict_package` Constructs 3-Way Diffs correctly
- **Description**: Ensure the `ConflictManager` correctly utilizes `git show` to extract the Base, Local, and Remote states of a conflicted file and constructs a pristine markdown prompt, avoiding reliance on `<<<<<<<` conflict markers.
- **Why**: This validates the fundamental shift in how the Master Integrator agent receives context, proving it has clean, uncorrupted code blocks to work with.

## Behavior Definitions

```gherkin
Feature: CycleState Constraints and Routing
  As the Workflow Orchestrator
  I want strictly typed state and deterministic routing
  So that the LangGraph executes the 5-Phase architecture reliably

  Scenario: CycleState validation catches invalid auditor index
    Given a new CycleState is initialized
    When the "current_auditor_index" is set to 0
    Then a Pydantic ValidationError should be raised

  Scenario: Sandbox Evaluator routes to Auditor during implementation
    Given a CycleState with a passing "sandbox_status"
    And "is_refactoring" is set to False
    When "route_sandbox_evaluate" is called
    Then it should return "auditor"

  Scenario: Sandbox Evaluator routes to Final Critic during refactoring
    Given a CycleState with a passing "sandbox_status"
    And "is_refactoring" is set to True
    When "route_sandbox_evaluate" is called
    Then it should return "final_critic"

  Scenario: Auditor routes to next auditor on approval
    Given a CycleState where the current auditor approved the code
    And the "current_auditor_index" is 1
    When "route_auditor" is called
    Then it should increment "current_auditor_index" to 2
    And it should return "next_auditor"

  Scenario: Auditor routes to pass_all on final approval
    Given a CycleState where the current auditor approved the code
    And the "current_auditor_index" is 3 (assuming max 3)
    When "route_auditor" is called
    Then it should return "pass_all"

Feature: 3-Way Diff Construction
  As the Master Integrator Agent
  I want clean Base, Local, and Remote code blocks
  So that I can resolve merge conflicts without parsing raw Git markers

  Scenario: Construct a 3-way diff from a conflicted file
    Given a Git repository with a merge conflict in "app.py"
    When "build_conflict_package" is called for "app.py"
    Then the resulting string should contain "### Base" followed by the original code
    And it should contain "### Branch A" followed by the local modifications
    And it should contain "### Branch B" followed by the remote modifications
    And it should not contain "<<<<<<<" or "======="
```