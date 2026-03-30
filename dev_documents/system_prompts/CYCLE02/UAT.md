# CYCLE02 User Acceptance Testing (UAT)

## Test Scenarios

The User Acceptance Testing strategy for CYCLE02 builds upon the interactive `marimo` notebook (`tutorials/nitpickers_5_phase_architecture.py`) established in CYCLE01. This cycle introduces the advanced orchestration of the Integration Phase (Phase 3) and the standalone User Acceptance Testing Phase (Phase 4). The UAT scenarios below are designed to be executable demonstrations of the system's ability to handle complex parallel merging, resolve 3-Way Diff conflicts, and utilise multi-modal diagnostics for E2E failures.

### Scenario ID: UAT-C02-01 (Priority: Critical)
**Title:** Integration Graph - 3-Way Diff Conflict Resolution
**Description:** This scenario validates the system's ability to intelligently resolve a simulated Git merge conflict using the newly implemented `ConflictManager` and `ConflictPackage` schema.
*   **Setup:** In "Mock Mode" within the Marimo notebook, we programmatically construct an `IntegrationState` representing a file with conflicting changes from two hypothetical parallel cycles (Branch A and Branch B). We provide mock string values for `base_code`, `local_code` (Branch A), and `remote_code` (Branch B).
*   **Execution:** We execute the `_create_integration_graph`. The mock `git_merge_node` intentionally flags a conflict. The graph must route to the `master_integrator_node`.
*   **Verification:** The user observes the specific prompt payload generated for the LLM. It must clearly separate the three code states according to the `ConflictPackage` schema, proving the system is no longer relying on raw `<<<<<<<` markers. We configure the mock Master Integrator to return a unified string. The graph must then route to the `global_sandbox_node` and eventually `END`. This demonstrates successful conflict resolution routing.

### Scenario ID: UAT-C02-02 (Priority: High)
**Title:** QA Graph - Multi-Modal Diagnostics and Remediation
**Description:** This scenario demonstrates the self-healing capability of Phase 4 (UAT & QA Graph) when an end-to-end UI test fails.
*   **Setup:** We instantiate a `QaState` and simulate a failed Playwright test execution. The mock state is populated with a simulated error log string and a mock Base64-encoded screenshot representing the UI failure.
*   **Execution:** We execute the `_create_qa_graph`. The graph routes the failure to the `qa_auditor` (an OpenRouter Vision model). In "Mock Mode," the mock auditor returns a structured JSON fix plan diagnosing the visual issue. The graph then routes to the `qa_session` to apply the "fix."
*   **Verification:** The user observes the graph looping back to re-evaluate the UAT test. Upon successful mock re-evaluation, the graph must successfully reach the `END` node. This confirms the multi-modal diagnostic loop operates independently of the Phase 2 implementation logic.

### Scenario ID: UAT-C02-03 (Priority: Medium)
**Title:** Pipeline Orchestration - Full 5-Phase Sequence
**Description:** This scenario serves as the ultimate demonstration of the entire NITPICKERS workflow, orchestrating Phase 2, 3, and 4 sequentially.
*   **Setup:** We use the `WorkflowService` to initiate `run_pipeline` with a mock configuration representing two simple parallel cycles.
*   **Execution:** All external calls (Git, LLMs, Sandbox) are mocked to return instantaneous success.
*   **Verification:** The user visually traces the logs outputted by the `WorkflowService`. The logs must definitively show:
    1.  Concurrent execution of the two Coder Graphs (Phase 2).
    2.  Sequential execution of the Integration Graph (Phase 3) *only after* both Coder tasks complete successfully.
    3.  Sequential execution of the QA Graph (Phase 4) *only after* the Integration Graph completes successfully.
    This scenario proves the overarching orchestration logic correctly manages the parallel-to-sequential transitions.

## Behavior Definitions

The following Gherkin-style definitions formalise the expected behaviour of the Phase 3 and Phase 4 graphs, dictating the requirements for the Marimo tutorial execution.

**Feature:** Phase 3 Integration Routing and Resolution
**As a** system orchestrator
**I want** the Integration Graph to handle merge conflicts intelligently using 3-Way Diffs
**So that** parallel development cycles can be merged safely and automatically

**Scenario:** Git Merge Conflict routes to Master Integrator
**GIVEN** the system is currently executing the Phase 3 Integration Graph
**AND** the `git_merge_node` encounters a merge conflict
**WHEN** the `route_merge` routing function is invoked
**THEN** the function must return the string literal `"master_integrator_node"`
**AND** the `ConflictManager` must extract the Base, Local, and Remote code states

**Scenario:** Successful Git Merge routes to Global Sandbox
**GIVEN** the system is currently executing the Phase 3 Integration Graph
**AND** the `git_merge_node` completes without conflicts
**WHEN** the `route_merge` routing function is invoked
**THEN** the function must return the string literal `"global_sandbox_node"`
**AND** the graph execution must perform full-system static and dynamic analysis

**Scenario:** Global Sandbox Failure routes to Master Integrator
**GIVEN** the system is currently executing the Phase 3 Integration Graph
**AND** the `global_sandbox_node` fails (indicating a regression introduced during integration)
**WHEN** the `route_global_sandbox` routing function is invoked
**THEN** the function must return the string literal `"master_integrator_node"`
**AND** the graph execution must loop back to resolve the integration bug

**Feature:** Phase 4 QA Remediation Loop
**As a** system orchestrator
**I want** the QA Graph to independently diagnose and fix E2E failures
**So that** the final deliverable is functionally flawless before completion

**Scenario:** Failed UAT Execution triggers QA Diagnostics
**GIVEN** the system is currently executing the Phase 4 QA Graph
**AND** the `uat_evaluate` node reports a test failure (with logs and/or screenshots)
**WHEN** the graph routing is evaluated
**THEN** the graph execution must transition to the `qa_auditor` node
**AND** the auditor must receive the multi-modal failure context

**Scenario:** QA Auditor outputs structured fix plan for Session
**GIVEN** the system is currently executing the `qa_auditor` node
**WHEN** the Vision LLM (or mock) completes its analysis
**THEN** it must return a structured JSON fix plan
**AND** the graph execution must transition to the `qa_session` node to implement the plan

**Scenario:** Successful UAT Execution concludes the pipeline
**GIVEN** the system is currently executing the Phase 4 QA Graph
**AND** the `uat_evaluate` node reports all tests passed
**WHEN** the graph routing is evaluated
**THEN** the graph execution must transition to the `END` node, concluding the 5-Phase pipeline