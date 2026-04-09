# User Acceptance Testing Plan: CYCLE01

## Test Scenarios

### Scenario 1: The 5-Phase Parallel Execution and Serial Auditing Workflow
**Priority:** High
**Description:**
This scenario validates the core functionality of the newly refactored Coder Graph (Phase 2), specifically ensuring that multiple development cycles can run concurrently without interference and that the serial auditing mechanism correctly processes the generated code. The test will simulate the creation of a simple utility function. We expect the system to successfully traverse the initial implementation (`coder_session`), pass the initial `sandbox_evaluate`, and correctly iterate through the sequential `auditor_node`s. The primary objective is to verify that the `current_auditor_index` increments correctly upon approval and that the `is_refactoring` state boolean is toggled accurately before the final self-critique. The test must demonstrate that the system avoids infinite loops by enforcing the `audit_attempt_count` limit. This scenario will be implemented as an interactive, executable tutorial block within the `tutorials/UAT_AND_TUTORIAL.py` Marimo notebook, utilizing mocked LLM responses to ensure rapid, deterministic execution in CI environments without incurring real API costs. The user will be able to visually trace the path of the state object as it moves through the graph.

### Scenario 2: The 3-Way Diff Integration and Conflict Resolution
**Priority:** Critical
**Description:**
This scenario is designed to stress-test the new Integration Graph (Phase 3) and the enhanced 3-Way Diff resolution capabilities of the Master Integrator agent. The test will programmatically create a mock repository state where a common ancestor (Base) file has been modified in two divergent ways by two simulated parallel feature branches (Branch A and Branch B), resulting in a direct Git merge conflict. The system must attempt the standard merge, detect the conflict, and correctly invoke the `master_integrator_node`. The crucial validation step is to examine the prompt constructed by the `ConflictManager`; it must accurately contain the contents of the Base, Local, and Remote versions of the conflicted file. The test will then mock the LLM's response with a successfully synthesized file, verifying that the system applies this resolution, commits the change, and successfully passes the subsequent `global_sandbox_node` evaluation. This scenario will also be embedded within the `tutorials/UAT_AND_TUTORIAL.py` Marimo notebook, providing a clear, interactive demonstration of the system's ability to self-heal complex integration issues autonomously.

## Behavior Definitions

**Feature:** 5-Phase Pipeline Orchestration and Conflict Resolution

**Scenario Outline:** Concurrent execution of Coder cycles with serial auditing
  **Given** the orchestrator is initialized with multiple independent feature requests
  **And** the `is_refactoring` flag is set to `False` for all cycles initially
  **When** the system triggers parallel execution of the `_create_coder_graph` for each request
  **Then** the Coder agent generates the initial implementation and unit tests
  **And** the `sandbox_evaluate` node validates the syntax and test execution successfully
  **And** the state is routed to the `auditor_node` based on the routing logic
  **And** the system sequentially invokes multiple independent auditors, incrementing `current_auditor_index` upon approval
  **And** upon successful approval from all auditors, the state transitions to the `refactor_node`
  **And** the `is_refactoring` flag is definitively set to `True`
  **And** the final logic is verified by the `final_critic_node` before completing Phase 2

**Scenario Outline:** Automated 3-Way Diff Conflict Resolution
  **Given** Phase 2 completes successfully for multiple cycles, resulting in divergent feature branches
  **And** the Integration Phase attempts to merge Branch A and Branch B into the integration branch
  **And** a Git merge conflict is detected within a specific file
  **When** the `master_integrator_node` is invoked
  **Then** the `ConflictManager` constructs a comprehensive diff package containing the Base, Local, and Remote file contents
  **And** the `ConflictManager` rigorously validates all file paths against the `workspace_root` to prevent directory traversal attacks
  **And** the Master Integrator agent synthesizes a unified resolution that resolves the conflict markers
  **And** the system successfully commits the resolved file to the integration branch
  **And** the `global_sandbox_node` successfully validates the fully integrated codebase without regressions

**Scenario Outline:** Separation of UAT from Implementation Phases
  **Given** the Orchestrator has successfully completed the Integration Phase (Phase 3)
  **When** the Orchestrator initiates the UAT & QA Graph (Phase 4)
  **Then** the system executes the comprehensive end-to-end testing suite against the integrated application
  **And** if an E2E test fails, the system captures rich multi-modal context (e.g., Playwright traces, DOM snapshots)
  **And** the `qa_auditor` analyzes the failure artifacts to formulate a diagnostic plan
  **And** the `qa_session` implements the necessary corrections within the integrated environment
  **And** the UAT suite is re-executed until all validations pass seamlessly, concluding the 5-phase pipeline.
