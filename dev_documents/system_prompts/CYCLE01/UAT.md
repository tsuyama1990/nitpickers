# UAT PLAN: CYCLE 01 - Serial Auditing Orchestration

## Test Scenarios

### Scenario ID: UAT-C01-01
**Priority:** High
**Description:** Verify the complete, successful traversal of the Phase 2 serial auditing graph without any rejections.
**Context:** The system must be able to smoothly transition from initial code generation, through multiple sequential auditors, through a refactoring node, and out via the final critic when all LLMs provide positive feedback. This represents the "happy path" of the autonomous development cycle, proving that the state management and routing logic allow code to reach completion when no flaws are detected. We must ensure the `is_refactoring` flag toggles correctly and that the `current_auditor_index` reaches its maximum configured value before advancing.

### Scenario ID: UAT-C01-02
**Priority:** High
**Description:** Verify the auditor rejection loop and the attempt threshold fallback.
**Context:** When an auditor rejects code, the graph must route back to the coder for modifications. If the same auditor rejects the code repeatedly (exceeding the `audit_attempt_count` threshold), the system must gracefully exit or pivot, preventing an infinite loop. This scenario verifies the robustness of the system against recalcitrant LLMs or unsolvable coding challenges, ensuring that the pipeline does not hang indefinitely and correctly escalates the failure state.

## Behavior Definitions

### UAT-C01-01: Successful Serial Traversal
**GIVEN** the LangGraph `_create_coder_graph` is initialized
**AND** all internal nodes (Coder, Sandbox, Auditors, Critic) are mocked to return successful/approved states immediately
**WHEN** the graph execution is invoked with a standard initialized `CycleState`
**THEN** the LangGraph execution trace should demonstrate sequential visitation of the nodes
**AND** the `current_auditor_index` in the final `CommitteeState` should increment from 1 to 3
**AND** the `is_refactoring` flag should toggle to `True` during the later stages of the trace
**AND** the final state returned by the graph should indicate successful completion of the Coder Phase without any error messages.

### UAT-C01-02: Rejection Loop and Fallback
**GIVEN** the LangGraph `_create_coder_graph` is initialized
**AND** the `auditor_node` is explicitly mocked to consistently return an unapproved `audit_result` across multiple invocations
**WHEN** the graph execution is invoked with a standard `CycleState`
**THEN** the graph should route back to the coder node upon the first rejection
**AND** the `audit_attempt_count` within the `CycleState` should increment sequentially on each pass
**AND** upon reaching the configured maximum attempt limit (e.g., 2 or 3), the `route_auditor` function should trigger a pivot or failure state transition
**AND** the graph execution should terminate gracefully, returning an error status indicating that the attempt threshold was exceeded, rather than falling into an infinite loop.
