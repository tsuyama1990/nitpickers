# UAT: Implement 5-Phase Architecture Redesign

## Test Scenarios

### Scenario ID: UAT-001 (Priority: High)
**Title:** Mock Mode Orchestration of 5-Phase Architecture
**Description:** This scenario validates that the orchestrating `WorkflowService` correctly instantiates and transitions through Phase 2 (Coder Graph), Phase 3 (Integration Graph), and Phase 4 (QA Graph) without making live LLM calls. It utilizes a Marimo notebook (`tutorials/UAT_AND_TUTORIAL.py`) operating in Mock Mode, ensuring all external APIs (e.g., OpenRouter, Jules, E2B) are monkey-patched to return deterministic responses. The execution must demonstrate parallel execution of multiple `CycleState` instances, verifying that `is_refactoring` toggles correctly and `current_auditor_index` increments sequentially up to the threshold. Once parallel cycles terminate successfully, the system must trigger a simulated `IntegrationState` merging, followed by the UAT phase. The user should observe clean state transitions via the Marimo UI, confirming zero state-bleed between concurrent cycles. This guarantees the architectural structural integrity is completely resilient to API unavailability in CI/CD pipelines.

### Scenario ID: UAT-002 (Priority: High)
**Title:** Real Mode 3-Way Diff Conflict Resolution
**Description:** This scenario executes the newly implemented 3-Way Diff mechanism using real API calls (Real Mode). A simulated multi-branch Git conflict is created programmatically within a temporary bare repository. Branch A modifies a target function to include logging, while Branch B modifies the same function to add error handling. The Marimo notebook invokes the `master_integrator_node` within Phase 3. The integration prompt must successfully build a payload containing the Base code, Local code (Branch A), and Remote code (Branch B). The LLM response is evaluated to ensure it generates a unified function incorporating both logging and error handling without destroying the underlying logic or producing invalid Git marker syntax. The user experiences the seamless integration of conflicting codes directly within the notebook, showcasing the system's robust integration capabilities.

## Behavior Definitions

**Feature:** 5-Phase Architecture Orchestration
As a system architect,
I want the AI agents to execute within strictly isolated, sequential phases (Init, Architect, Coder, Integration, QA),
So that parallel development cycles do not corrupt the global repository state and conflicts are resolved deterministically.

**Scenario:** Successful parallel execution of Phase 2 transitions into Phase 3
  **Given** the user has initialized the project (`nitpick init`) and defined `ALL_SPEC.md`
  **And** Phase 1 (Architect Phase) has generated two distinct `CycleState` configurations (Cycle 01 and Cycle 02)
  **When** the user executes `nitpick run-pipeline`
  **Then** the `WorkflowService` must run Cycle 01 and Cycle 02 concurrently in isolated sandboxes
  **And** each cycle must independently sequence through its Auditor chain, incrementing `current_auditor_index` until approved
  **And** upon successful termination of both cycles, Phase 3 (Integration Phase) must be triggered sequentially
  **And** `git_merge_node` must attempt to unify the changes into the master branch

**Scenario:** 3-Way Diff Conflict Resolution in Phase 3
  **Given** Phase 3 (Integration Phase) is executing
  **And** a Git merge conflict occurs between Cycle 01 (Local) and Cycle 02 (Remote) against a common Base
  **When** the conflict is detected by `route_merge`
  **Then** the workflow must transition to the `master_integrator_node`
  **And** the `build_conflict_package` must construct a prompt containing the explicit blocks: "Base (元のコード)", "Branch A の変更 (Local)", and "Branch B の変更 (Remote)"
  **And** the Master Integrator LLM must return a synthesized, conflict-free code block
  **And** the system must successfully apply this code block and proceed to `global_sandbox_node`

**Scenario:** QA Graph Execution in Phase 4
  **Given** Phase 3 (Integration Phase) has completed successfully and all code is merged
  **When** the workflow transitions to Phase 4 (UAT & QA Graph)
  **Then** the system must execute the E2E Playwright tests defined in the UAT scenarios
  **And** if a test fails, it must route to `qa_auditor` for diagnosis and subsequent `qa_session` for automated remediation
  **And** the pipeline must finally terminate with an overall `END` state, signifying development completion.

### Scenario ID: UAT-003 (Priority: Medium)
**Title:** Auditor Rejection Cycle Limitation
**Description:** This scenario validates that the Phase 2 (Coder Graph) auditor loops function effectively while preventing infinite retry patterns. A deterministic state is induced where the primary OpenRouter `auditor_node` consistently returns `"reject"` when evaluating a proposed function. The test monitors the `audit_attempt_count` variable. Upon reaching the maximum allowed attempts (e.g., 2), the router (`route_auditor`) must enforce a fallback strategy, overriding the rejection loop and transitioning the system to either a forced pass or an escalated failure state. This ensures that the overall cycle pipeline remains resilient and does not consume excessive compute or API resources during unresolvable architectural disputes. The user verifies the `audit_attempt_count` variable caps out and breaks the cycle loop as expected within the LangGraph UI or Marimo notebook log outputs.

**Scenario:** Auditor Retry Limit Enforcement
  **Given** Phase 2 (Coder Graph) is running a `CycleState` with a complex feature implementation
  **And** the `auditor_node` repeatedly evaluates the implementation as sub-optimal, yielding a `"reject"` response
  **When** the `audit_attempt_count` increments iteratively
  **Then** the `route_auditor` must intercept the routing logic when `audit_attempt_count` equals the predefined threshold
  **And** the system must terminate the infinite loop, returning a designated fallback response instead of `next_auditor`
