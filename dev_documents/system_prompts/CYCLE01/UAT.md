# CYCLE01 UAT: The Coder Graph Evolution (Phases 1 & 2)

## Test Scenarios

These scenarios are meticulously designed to validate the core structural shift of the Coder Phase: the strict enforcement of a sequential auditing process (`Auditor 1 -> 2 -> 3`), a dedicated refactoring loop, and the complete elimination of parallel, conflicting feedback loops. The successful execution of these tests guarantees that the system's routing logic is robust and that agents will not become trapped in infinite loops or confused by simultaneous, contradictory critiques. These tests will be executed within the interactive `tutorials/UAT_AND_TUTORIAL.py` Marimo notebook, providing both automated CI validation and an interactive tutorial experience for developers.

### Scenario ID: UAT-C01-001
*   **Priority**: High
*   **Title**: Sequential Auditor Approval Path
*   **Description**: This is the "happy path" scenario that verifies the fundamental correctness of the new serial auditing pipeline. It tests whether a newly generated piece of code (for example, a simple Python utility function to calculate the Fibonacci sequence) correctly passes through the initial Sandbox evaluation (linters and basic tests), receives sequential, un-interrupted approvals from Auditor 1 (e.g., Logic Review), Auditor 2 (e.g., Security Review), and Auditor 3 (e.g., Performance Review), and correctly transitions into the dedicated Refactoring Loop before final validation. The critical element here is proving that the `current_auditor_index` increments correctly and that the workflow does not prematurely exit the auditing phase before all required checks are complete.
*   **Execution Strategy**: To ensure this test runs reliably in CI environments without incurring API costs or requiring live credentials, it must utilize the "Mock Mode" implemented within the Marimo notebook. The notebook must inject `pytest.MonkeyPatch` overrides or utilize a dependency injection container to swap out the real `auditor_node` with a deterministic mock function. This mock function will be programmed to immediately return an "Approve" decision for each sequential call, artificially incrementing the `current_auditor_index` in the `CycleState`.
*   **Validation Point**: The primary assertion is a strict examination of the LangGraph state trace. The trace must definitively show the exact sequential path: `coder_session` -> `sandbox_evaluate` -> `auditor_node` (index 1) -> `auditor_node` (index 2) -> `auditor_node` (index 3) -> `refactor_node` -> `sandbox_evaluate` -> `final_critic_node` -> `END`. Furthermore, the test must explicitly assert that the `is_refactoring` boolean flag within the `CycleState` evaluates to `True` at the exact moment the workflow enters the second `sandbox_evaluate` node, proving the transition logic is sound.

### Scenario ID: UAT-C01-002
*   **Priority**: High
*   **Title**: Auditor Rejection and Retry Limit (Infinite Loop Prevention)
*   **Description**: This scenario tests the system's resilience and its ability to handle failure gracefully. It ensures the routing logic correctly handles a rejection from any Auditor in the chain. Instead of proceeding to subsequent auditors with flawed code, the system must immediately route back to the Coder for remediation. Most importantly, it verifies the "circuit breaker" mechanism: if an Auditor repeatedly rejects the code (simulating a complex logic error the Coder cannot resolve), the system must halt or escalate after reaching the predefined `audit_attempt_count` limit (e.g., 2 attempts). This prevents the agent from entering an expensive, infinite retry loop.
*   **Execution Strategy**: In "Mock Mode", the Marimo notebook will configure the mocked `auditor_node` to consistently return a "Reject" response, specifically when the `current_auditor_index` is 1. The test will run the graph. The expected behavior is that the mock auditor rejects the initial code, the workflow routes back to the mock coder, the mock coder "fixes" the code (passing the sandbox), but the mock auditor rejects it a second time.
*   **Validation Point**: The state trace must definitively show the circuit breaker activating: `coder_session` -> `sandbox_evaluate` -> `auditor_node` (index 1, Rejects) -> `coder_session` -> `sandbox_evaluate` -> `auditor_node` (index 1, Rejects again) -> (Fallback State, Error Node, or Terminal Escalation based on final implementation). The test must assert that the `audit_attempt_count` increments to 2, the graph terminates or escalates appropriately, and crucially, the `current_auditor_index` remains at 1 (proving it never proceeded to Auditor 2).

### Scenario ID: UAT-C01-003
*   **Priority**: Medium
*   **Title**: Refactoring Loop Toggle and Final Critique
*   **Description**: This scenario isolates and confirms the precise mechanical action of the `refactor_node`. Its sole purpose is to verify that this node successfully toggles the `is_refactoring` state flag to `True` upon completing its code cleanup tasks. This seemingly simple toggle is the linchpin of the 5-Phase Architecture's safety mechanism; it ensures that the subsequent pass through the `sandbox_evaluate` node correctly routes to the `final_critic_node` (for final sign-off before integration) instead of erroneously looping back into the `auditor_node` chain.
*   **Execution Strategy**: In "Mock Mode", the test will initialize a `CycleState` directly at the stage just prior to refactoring (e.g., setting `current_auditor_index` to 4, indicating all audits have passed). The graph is executed. The test observes the state mutation directly after the mocked `refactor_node` executes its operation.
*   **Validation Point**: The test contains two critical assertions. First, it must assert that `state["is_refactoring"] == True` immediately after the `refactor_node` completes. Second, it must explicitly call the `route_sandbox_evaluate` routing function with this mutated state and assert that the function returns the exact string `"final_critic"`, proving the conditional edge logic correctly interprets the flag.

## Behavior Definitions (Gherkin)

The following Gherkin definitions provide a human-readable, executable specification for the core behaviors expected from the newly refactored Coder Graph. They serve as the definitive contract for the routing logic, ensuring that all edge cases regarding sequential auditing, refactoring loops, and infinite loop prevention are explicitly defined and testable by the development team. These definitions form the basis for the automated tests implemented in the Marimo notebook.

**Feature: Sequential Coder Graph Execution and Refactoring Loops**

As a System Architect managing autonomous AI agents,
I want the Coder Graph to enforce a strict, sequential auditing process and a dedicated refactoring phase,
So that I can prevent parallel feedback conflicts, ensure code quality, and guarantee the system does not enter infinite execution loops.

**Scenario: Successful Implementation, Sequential Auditing, and Final Refactoring**
*   **GIVEN** the system initializes a new `CycleState` object containing a valid, unambiguous feature requirement
*   **AND** the `is_refactoring` flag is explicitly set to `False`
*   **AND** the `current_auditor_index` is explicitly set to `1`
*   **WHEN** the orchestrator triggers the execution of the `_create_coder_graph`
*   **AND** the initial code generation by the `coder_session` successfully passes the `sandbox_evaluate` structural checks
*   **AND** the sequential review process begins, and Auditor 1 reviews and explicitly approves the implementation
*   **AND** the system increments the index, and Auditor 2 reviews and explicitly approves the implementation
*   **AND** the system increments the index, and Auditor 3 (the final auditor) reviews and explicitly approves the implementation
*   **THEN** the routing logic must transition the workflow out of the auditing loop and into the `refactor_node`
*   **AND** the `refactor_node` must successfully execute and subsequently set the `is_refactoring` state flag to `True`
*   **WHEN** the refactored code is routed back through the `sandbox_evaluate` node and passes all structural checks
*   **THEN** the routing logic, detecting the `is_refactoring` flag is `True`, must bypass the auditors and transition to the `final_critic_node`
*   **AND** upon final approval, the workflow must successfully complete and reach the terminal `END` state.

**Scenario: Auditor Rejection, Remediation Loop, and Infinite Loop Prevention (Circuit Breaker)**
*   **GIVEN** the system initializes a new `CycleState` object containing a valid feature requirement
*   **AND** the `audit_attempt_count` is explicitly set to `0`
*   **WHEN** the orchestrator triggers the execution of the `_create_coder_graph`
*   **AND** the initial code generation by the `coder_session` successfully passes the `sandbox_evaluate` structural checks
*   **AND** the workflow transitions to Auditor 1, but Auditor 1 detects a critical flaw and explicitly rejects the implementation
*   **THEN** the routing logic must transition the workflow immediately back to the `coder_session` for remediation
*   **AND** the `audit_attempt_count` must increment by exactly 1 (becoming 1)
*   **AND** the `current_auditor_index` must remain at 1, preventing progression to Auditor 2
*   **WHEN** the `coder_session` submits a revised code attempt, and it successfully passes the `sandbox_evaluate` structural checks
*   **AND** the workflow transitions back to Auditor 1, but Auditor 1 rejects the revised implementation a second time
*   **THEN** the `audit_attempt_count` must increment by exactly 1 (becoming 2, reaching the maximum threshold)
*   **AND** the routing logic must activate the circuit breaker, transitioning the workflow to an escalation or terminal error state
*   **AND** the workflow must immediately halt, explicitly preventing an infinite loop and ensuring it never proceeds to Auditor 2 or Auditor 3.