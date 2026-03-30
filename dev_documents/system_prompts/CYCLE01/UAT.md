# CYCLE01 UAT Plan: Foundational State and Coder Graph Refactoring

## Test Scenarios

### Scenario ID: UAT-C1-001 (Priority: High)
**Objective:** Verify the structural integrity and execution flow of the newly implemented 5-Phase Coder Graph (`_create_coder_graph`), specifically ensuring that the serial auditing loop and the `is_refactoring` gate function correctly in a controlled, simulated environment.

**Description:** This scenario will utilize the interactive `tutorials/nitpickers_5_phase_architecture.py` Marimo notebook to visually demonstrate the flow of data through the Coder Graph. The notebook will be configured to operate in "Mock Mode," meaning all external LLM API calls (e.g., OpenRouter, Google/Jules) and E2B sandbox executions will be bypassed using `pytest.MonkeyPatch` context managers or specific environment variable overrides. Instead, deterministic, pre-programmed responses will be returned by the mocked nodes. This allows the user to step through the graph execution and observe the precise mutations of the `CycleState` object without incurring API costs or requiring complex environment setups.

**Steps to Execute:**
1.  Open the `tutorials/nitpickers_5_phase_architecture.py` notebook using `uv run marimo edit`.
2.  Navigate to the section titled "Phase 1 & 2: The Coder Graph & Serial Auditing".
3.  Ensure the "Execution Mode" toggle is set to "Mock Mode".
4.  Execute the initial setup cell, which instantiates a fresh `CycleState` object representing a simple feature request (e.g., "Implement a basic calculator class").
5.  Execute the cell containing the `_create_coder_graph` traversal loop. The notebook will display the sequence of executed nodes and the corresponding state changes at each step.
6.  Observe the output carefully. The trace should clearly show the system passing through the `coder_session`, `sandbox_evaluate`, and entering the `auditor_node` loop. The notebook must explicitly highlight the `current_auditor_index` incrementing from 1 to 3 upon consecutive "Approve" responses from the mocked auditors.
7.  After the third auditor approval, verify that the execution transitions to the `refactor_node`. The notebook must explicitly highlight the `is_refactoring` flag toggling from `False` to `True`.
8.  Verify that subsequent passes through `sandbox_evaluate` (with `is_refactoring=True`) correctly route to the `final_critic_node` instead of returning to the auditor loop.
9.  Finally, verify that the graph execution successfully concludes at the `END` node upon a simulated "Approve" response from the final critic.

### Scenario ID: UAT-C1-002 (Priority: Medium)
**Objective:** Validate the fallback and failure mechanisms of the Coder Graph, specifically ensuring that infinite loops are prevented when an auditor repeatedly rejects the implementation, and that sandbox failures correctly route back to the coder session.

**Description:** This scenario will again utilize the "Mock Mode" of the `tutorials/nitpickers_5_phase_architecture.py` notebook. However, the mock responses will be deliberately configured to simulate failure conditions. This will demonstrate the system's ability to handle adversity and gracefully recover or terminate within defined boundaries.

**Steps to Execute:**
1.  In the Marimo notebook, navigate to the "Advanced Coder Scenarios" section.
2.  Execute the cell configuring the mock nodes to simulate a "Sandbox Failure" (e.g., a syntax error in the generated code).
3.  Execute the graph traversal cell. Verify that the trace shows execution returning immediately from `sandbox_evaluate` to `coder_session` without entering the auditor loop.
4.  Execute the cell configuring the mock nodes to simulate an "Auditor Rejection Loop." The mocked auditor will consistently return a "Reject" response.
5.  Execute the graph traversal cell. Observe the trace. The execution should route back to `coder_session` and then back through `sandbox_evaluate` to the `auditor_node`.
6.  The crucial validation is observing the `audit_attempt_count` incrementing. The notebook must demonstrate that after a predefined maximum number of attempts (e.g., 2), the system either forces a progression, escalates to a human, or cleanly terminates the cycle with an error state, preventing an infinite execution loop.

## Behavior Definitions

**Feature: Strict Pydantic State Management**

  **Scenario: Instantiating CycleState with correct types**
    GIVEN the system requires a new development cycle state
    WHEN a `CycleState` object is instantiated with a valid string `task_description`, default boolean `is_refactoring`, and default integer `current_auditor_index`
    THEN the instantiation succeeds without raising any validation errors
    AND the `is_refactoring` attribute is strictly `False`
    AND the `current_auditor_index` attribute is exactly `1`
    AND the `audit_attempt_count` attribute is exactly `0`

  **Scenario: Preventing invalid state mutations**
    GIVEN an existing, successfully instantiated `CycleState` object named `current_state`
    WHEN a process attempts to reassign the `is_refactoring` attribute to an invalid type, such as the string `"True"` instead of the boolean `True`
    THEN a Pydantic `ValidationError` is immediately raised
    AND the `current_state` remains unchanged, preserving its integrity

  **Scenario: Enforcing state immutability**
    GIVEN an existing, successfully instantiated `CycleState` object named `current_state`
    WHEN a process attempts to directly mutate an attribute, such as executing `current_state.audit_attempt_count = 5`
    THEN a Pydantic `ValidationError` (or similar immutability error resulting from `frozen=True`) is immediately raised
    AND the system log explicitly records the unauthorized mutation attempt

**Feature: Conditional Graph Routing Logic**

  **Scenario: Routing after a successful sandbox evaluation during primary implementation**
    GIVEN the execution is currently at the `sandbox_evaluate` node
    AND the current `CycleState` indicates a `sandbox_status` of `"success"`
    AND the `is_refactoring` flag is set to `False`
    WHEN the `route_sandbox_evaluate` function is invoked
    THEN the function returns the exact string `"auditor"`
    AND the LangGraph orchestrator transitions execution to the `auditor_node`

  **Scenario: Routing after a failed sandbox evaluation**
    GIVEN the execution is currently at the `sandbox_evaluate` node
    AND the current `CycleState` indicates a `sandbox_status` of `"failed"`
    WHEN the `route_sandbox_evaluate` function is invoked
    THEN the function returns the exact string `"failed"`
    AND the LangGraph orchestrator transitions execution back to the `coder_session` node, regardless of the `is_refactoring` flag's state

  **Scenario: Routing after a successful sandbox evaluation during structural polish**
    GIVEN the execution is currently at the `sandbox_evaluate` node
    AND the current `CycleState` indicates a `sandbox_status` of `"success"`
    AND the `is_refactoring` flag is set to `True`
    WHEN the `route_sandbox_evaluate` function is invoked
    THEN the function returns the exact string `"final_critic"`
    AND the LangGraph orchestrator transitions execution to the `final_critic_node`

  **Scenario: Managing the serial auditor progression**
    GIVEN the execution is currently at the `auditor_node`
    AND the auditor has provided an "Approve" evaluation
    AND the current `CycleState` indicates a `current_auditor_index` of `2`
    WHEN the `route_auditor` function is invoked
    THEN the function returns the exact string `"next_auditor"`
    AND the subsequent state mutation increments `current_auditor_index` to `3`
    AND the LangGraph orchestrator loops execution back to the `auditor_node` for the final review

  **Scenario: Completing the serial auditor loop**
    GIVEN the execution is currently at the `auditor_node`
    AND the auditor has provided an "Approve" evaluation
    AND the current `CycleState` indicates a `current_auditor_index` of `3`
    WHEN the `route_auditor` function is invoked
    THEN the function returns the exact string `"pass_all"`
    AND the LangGraph orchestrator transitions execution to the `refactor_node`