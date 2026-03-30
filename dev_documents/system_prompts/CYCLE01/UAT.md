# CYCLE01 User Acceptance Testing (UAT)

## Test Scenarios

The User Acceptance Testing strategy for the 5-Phase Architecture is focused on providing an interactive, verifiable, and educational experience. We utilise `marimo` notebooks to allow the user (or automated CI pipelines) to execute and observe the system's behaviour step-by-step. The UAT for CYCLE01 specifically targets the Phase 2 Coder Graph, ensuring that its complex routing, serial auditing, and refactoring loops operate as intended under various simulated conditions. This guarantees that the foundation is rock-solid before integrating multiple cycles in Phase 3. The `tutorials/nitpickers_5_phase_architecture.py` notebook will contain all of these scenarios.

### Scenario ID: UAT-C01-01 (Priority: High)
**Title:** Coder Graph - Successful Single Iteration Loop
**Description:** This scenario verifies the "happy path" of the Phase 2 Coder Graph. The objective is to demonstrate that a well-formed feature request can traverse the entire Coder Graph sequentially—from initial implementation, through a successful local sandbox evaluation, past all three serial auditors without rejection, through the final refactoring node, and ultimately receiving approval from the final critic. This scenario is executed in "Mock Mode," where the LLM agents (Coder, Critic, Auditor) and the Sandbox are replaced with deterministic `AsyncMock` objects that consistently return positive results. The user should observe the `CycleState` progressing smoothly, specifically noting the `current_auditor_index` incrementing from 1 to 3, the `is_refactoring` flag toggling to `True` after the third auditor, and the final transition to the `END` node. This confirms the fundamental routing logic is sound and the state machine operates correctly under optimal conditions.

### Scenario ID: UAT-C01-02 (Priority: Critical)
**Title:** Coder Graph - Auditor Rejection and Remediation Loop
**Description:** This scenario tests the system's resilience and its ability to handle imperfect implementations. The objective is to verify that when a serial auditor identifies an issue, the Coder Graph correctly routes the cycle back to the `coder_session` for remediation, rather than proceeding to the next auditor or the refactoring phase. Using "Mock Mode," the scenario configures the first auditor (`current_auditor_index=1`) to intentionally reject the initial implementation, incrementing the `audit_attempt_count`. The graph must route back to the Coder. The scenario then configures the mock Coder to apply a "fix," and subsequent mock auditors are instructed to approve the changes. The user should observe the graph looping back to the implementation phase precisely once, demonstrating the system's capacity for self-correction before successfully navigating the remainder of the audit chain and reaching the `END` node. This validates the conditional routing (`route_auditor`) and the state mutation logic associated with rejections.

## Behavior Definitions

The following Gherkin-style definitions formalise the expected behaviour of the Phase 2 Coder Graph under specific conditions. These behaviours dictate the requirements for the `marimo` tutorial execution.

**Feature:** Phase 2 Coder Graph Routing
**As a** system orchestrator
**I want** the Coder Graph to correctly route execution based on sandbox and auditor feedback
**So that** only thoroughly validated and audited code progresses to the Integration Phase

**Scenario:** Successful Sandbox Evaluation routes to Serial Auditors
**GIVEN** the system is currently executing the Phase 2 Coder Graph
**AND** the `sandbox_evaluate` node has completed successfully
**AND** the `CycleState` flag `is_refactoring` is `False`
**WHEN** the `route_sandbox_evaluate` routing function is invoked
**THEN** the function must return the string literal `"auditor_node"`
**AND** the graph execution must transition to the serial auditor chain

**Scenario:** Failed Sandbox Evaluation routes back to Implementation
**GIVEN** the system is currently executing the Phase 2 Coder Graph
**AND** the `sandbox_evaluate` node has failed (e.g., linting errors or test failures)
**WHEN** the `route_sandbox_evaluate` routing function is invoked
**THEN** the function must return the string literal `"coder_session"`
**AND** the graph execution must transition back to the Coder for immediate remediation

**Scenario:** Serial Auditor Approval increments the Index
**GIVEN** the system is currently executing the `auditor_node` within the Phase 2 Coder Graph
**AND** the OpenRouter model (or mock) returns an "Approve" status
**AND** the current `CycleState` field `current_auditor_index` is less than 3
**WHEN** the `route_auditor` routing function is invoked
**THEN** the `CycleState` field `current_auditor_index` must be incremented by 1
**AND** the function must return the string literal `"next_auditor"`
**AND** the graph execution must loop back to the `auditor_node` for the next review

**Scenario:** Final Serial Auditor Approval triggers Refactoring
**GIVEN** the system is currently executing the `auditor_node` within the Phase 2 Coder Graph
**AND** the OpenRouter model (or mock) returns an "Approve" status
**AND** the current `CycleState` field `current_auditor_index` is exactly 3
**WHEN** the `route_auditor` routing function is invoked
**THEN** the function must return the string literal `"pass_all"`
**AND** the graph execution must transition to the `refactor_node`

**Scenario:** Refactoring Node updates State and loops to Sandbox
**GIVEN** the system is currently executing the `refactor_node` within the Phase 2 Coder Graph
**WHEN** the node logic completes its execution
**THEN** the `CycleState` flag `is_refactoring` MUST be updated to `True`
**AND** the graph execution must transition unconditionally back to the `sandbox_evaluate` node

**Scenario:** Post-Refactoring Sandbox Evaluation routes to Final Critic
**GIVEN** the system is currently executing the Phase 2 Coder Graph
**AND** the `sandbox_evaluate` node has completed successfully
**AND** the `CycleState` flag `is_refactoring` is `True`
**WHEN** the `route_sandbox_evaluate` routing function is invoked
**THEN** the function must return the string literal `"final_critic"`
**AND** the graph execution must transition to the final self-review phase