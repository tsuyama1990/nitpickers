# CYCLE01 UAT: Coder Graph & Serial Auditing

## Test Scenarios

### Scenario ID: Coder_Phase_01 - Happy Path Serial Audit
- **Priority**: High
- **Description**: Verify that the Coder Graph successfully executes a complete, uninterrupted "Happy Path" cycle. This scenario ensures the foundational LangGraph routing operates correctly. The system must initialize a cycle, generate initial code via the Coder agent, pass the local Sandbox evaluation, sequentially traverse three independent Auditor agents (Auditor 1 -> 2 -> 3) without any rejections, proceed to the Refactor node to set the `is_refactoring` flag to `True`, pass the final Sandbox evaluation, and receive approval from the Final Critic, resulting in a successfully completed cycle state.
- **Verification**: The LangGraph state at the `END` node must reflect `status="completed"`, `is_refactoring=True`, and `current_auditor_index=3` (or equivalent maximum). The execution trace (LangSmith or internal logger) must show the exact sequence of nodes visited.

### Scenario ID: Coder_Phase_02 - Auditor Rejection Loop
- **Priority**: High
- **Description**: Verify that the Coder Graph correctly handles a scenario where an Auditor agent rejects the proposed code. This test ensures the `audit_attempt_count` is functioning as a circuit breaker and the routing logic correctly loops back to the Coder. The system must initialize a cycle, pass the initial Sandbox, and reach the first Auditor. The Auditor must explicitly reject the code. The system must then route back to the Coder agent, incrementing the `audit_attempt_count`. After the Coder revises the code and passes the Sandbox again, the same Auditor must review the code. If approved on the second attempt, the system must proceed to the next Auditor.
- **Verification**: The LangGraph trace must show the sequence: `... -> auditor_node -> (reject) -> coder_session -> ... -> sandbox_evaluate -> auditor_node -> (approve) -> ...`. The `audit_attempt_count` must be incremented during the rejection cycle and the cycle must ultimately succeed if subsequent reviews pass.

### Scenario ID: Coder_Phase_03 - Refactoring Sandbox Failure
- **Priority**: Medium
- **Description**: Verify that the Coder Graph correctly handles a Sandbox evaluation failure that occurs *after* the refactoring node. This ensures that the system differentiates between initial implementation failures and post-refactoring regressions. The system must complete the initial implementation and serial audit successfully. Upon reaching the Refactor node, it must intentionally introduce a syntax error or a failing test case (simulated for the test). The subsequent Sandbox evaluation must fail. The routing logic must detect `is_refactoring=True` and route the failure back to the Coder for correction, rather than restarting the entire audit process.
- **Verification**: The LangGraph trace must show the sequence: `... -> refactor_node -> sandbox_evaluate -> (failed) -> coder_session -> ...`. The final state must successfully recover and complete the cycle after the Coder fixes the refactoring error.

## Behavior Definitions

### Feature: Serial Auditing & Refactoring Loop
As an AI-native development system,
I want to ensure that generated code passes through a strict sequence of independent reviews and a dedicated refactoring phase,
So that I can guarantee high quality, maintainable, and robust code before integration.

**Background:**
Given the system has successfully initialized Phase 0 and Phase 1,
And the Architect has defined at least one executable development cycle (`CYCLE01`).

**Scenario: Successful execution of the full Coder Phase**
- Given the system starts Phase 2 for `CYCLE01`
- And the Coder agent generates valid code that passes initial Sandbox evaluation
- When the first Auditor reviews the code
- And the first Auditor approves the code
- And the second Auditor reviews and approves the code
- And the third Auditor reviews and approves the code
- Then the system routes the cycle to the Refactor node
- And the system updates the state to `is_refactoring=True`
- And the Refactored code passes the final Sandbox evaluation
- And the Final Critic approves the code
- Then the Coder Phase completes successfully.

**Scenario: Auditor Rejection triggers a revision loop**
- Given the system is executing Phase 2 for `CYCLE01`
- And the code has passed the initial Sandbox evaluation
- And the first Auditor reviews the code
- When the first Auditor rejects the code due to a logic flaw
- Then the system increments the `audit_attempt_count` by 1
- And the system routes the cycle back to the Coder agent for revision
- And the Coder agent generates revised code that passes Sandbox evaluation
- When the first Auditor reviews the revised code and approves it
- Then the system proceeds to the second Auditor.

**Scenario: Refactoring introduces a regression**
- Given the system has successfully passed all Auditors
- And the system is executing the Refactor node
- When the Refactor node introduces a change that breaks a unit test
- And the subsequent Sandbox evaluation fails
- Then the system routes the cycle back to the Coder agent for correction
- And the system maintains the state `is_refactoring=True`
- And the Coder agent fixes the regression
- And the revised Refactored code passes Sandbox evaluation
- Then the system routes the cycle directly to the Final Critic node.