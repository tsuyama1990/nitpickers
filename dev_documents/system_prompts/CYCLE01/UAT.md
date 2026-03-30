# UAT: CYCLE01 - The Coder Graph & State Foundation

## Test Scenarios

To ensure the seamless integration and stability of the new 5-Phase Architecture, we must rigorously validate the Coder Graph (Phase 2) using interactive, reproducible User Acceptance Testing. This UAT will be executed via a dedicated `marimo` notebook (`tutorials/UAT_AND_TUTORIAL.py`). By employing `marimo`, users and CI pipelines can visually verify the system's behavior without wrestling with complex CLI setups or scattered logs.

The goal of this specific cycle's UAT is to demonstrate the resilience of the serial auditing loop and the robust state management introduced in `CycleState`. We will simulate a complete Coder Phase execution, proving that the worker agent cannot bypass the strict validation gates.

### Scenario ID: UAT-C01-01 - Mock Serial Auditing Loop
-   **Priority:** High
-   **Description:** This scenario validates the core looping mechanism of Phase 2. We will programmatically inject a mock feature request into a synthesized `CycleState`. The `marimo` notebook will execute the `_create_coder_graph` in **Mock Mode** (preventing real API calls to Jules or OpenRouter). We will configure the mock `auditor_node` to intentionally reject the first attempt, forcing the graph to route back to the `coder_session`. On the second attempt, the mock auditor will approve, incrementing the `current_auditor_index`. We will trace the state transitions visually in the notebook, proving that `audit_attempt_count` increments correctly and that the system transitions to the `refactor_node` only after all simulated auditors have passed. This ensures the foundational routing logic is sound without incurring API costs.

### Scenario ID: UAT-C01-02 - Live Sandbox Evaluation Gate
-   **Priority:** Medium
-   **Description:** This scenario demonstrates the system's ability to execute a real, albeit simple, implementation task using Live Mode. The user will provide their `.env` credentials. The `marimo` notebook will instruct the `coder_session` to generate a rudimentary Python function with an intentional linting error. We will execute the graph and observe the `sandbox_evaluate` node failing the code. The notebook must clearly display the "failed" route being taken back to the `coder_session`. Subsequently, the notebook will instruct the LLM to fix the error, passing the sandbox, and entering the serial audit phase. This scenario proves that the mechanical blockade is active and effective in a live environment.

## Behavior Definitions

The following Gherkin-style definitions formalize the expected behavior of the Coder Graph routing logic and state management. These definitions serve as the contractual agreement for the system's execution flow.

**Feature:** Serial Auditing and Refactoring Loop

  As a System Architect
  I want the Coder Graph to enforce strict serial auditing and refactoring loops
  So that AI-generated code is thoroughly reviewed and polished before integration.

  **Scenario:** Auditor Rejection Triggers Rework
    **Given** the Coder Graph is executing a cycle
    **And** the `sandbox_evaluate` node has successfully passed
    **And** the state `is_refactoring` is `False`
    **When** the current `auditor_node` returns a "Reject" status
    **Then** the `audit_attempt_count` in `CommitteeState` must increment by 1
    **And** the graph must route back to the `coder_session` node for rework.

  **Scenario:** Auditor Approval Advances the Index
    **Given** the Coder Graph is executing a cycle
    **And** the `sandbox_evaluate` node has successfully passed
    **And** the current `auditor_node` returns an "Approve" status
    **When** the routing logic evaluates the state
    **Then** the `current_auditor_index` in `CommitteeState` must increment by 1
    **And** the graph must route to the `auditor_node` again (Next Auditor) if the index is less than or equal to `NITPICK_MAX_AUDITORS`.

  **Scenario:** Passing All Auditors Triggers Refactoring
    **Given** the Coder Graph is executing a cycle
    **And** the `sandbox_evaluate` node has successfully passed
    **And** the current `auditor_node` returns an "Approve" status
    **When** the `current_auditor_index` exceeds `NITPICK_MAX_AUDITORS`
    **Then** the routing logic must return "pass_all"
    **And** the graph must route to the `refactor_node`.

  **Scenario:** Refactoring Phase Completion
    **Given** the Coder Graph has entered the refactoring phase
    **And** the `refactor_node` sets `is_refactoring` to `True`
    **When** the subsequent `sandbox_evaluate` node passes successfully
    **Then** the routing logic must evaluate `is_refactoring == True`
    **And** return "final_critic"
    **And** the graph must route to the `final_critic_node`.

  **Scenario:** Final Critic Approval Ends Phase
    **Given** the Coder Graph is at the `final_critic_node`
    **When** the self-evaluation returns "Approve"
    **Then** the routing logic must return "approve"
    **And** the graph must reach the `END` state for this specific cycle.
