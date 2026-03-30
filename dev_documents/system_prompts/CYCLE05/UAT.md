# CYCLE 05: CLI & Workflow Orchestration UAT

## Test Scenarios

### Scenario ID: UAT-05-01 (Priority: High)
**Description:** Verify the `run_full_pipeline` method orchestrates Phase 2 (Concurrent Coder), Phase 3 (Integration), and Phase 4 (QA) in the exact necessary sequence.
**Setup:** A Marimo notebook executing the `WorkflowService.run_full_pipeline` directly using `pytest.MonkeyPatch` to simulate deterministic `ainvoke` responses from the underlying LangGraph builders.
**Execution (Mock Mode):**
*   Initialize `WorkflowService` and mock its `GraphBuilder` instance.
*   Mock `build_coder_graph().ainvoke` to simulate a 1-second delay and return success.
*   Mock `build_integration_graph().ainvoke` to return success.
*   Mock `build_qa_graph().ainvoke` to return success.
*   Provide a dummy `CycleManifest` containing two planned cycles.
*   Execute `run_full_pipeline()`.
**Verification:**
*   Both `coder_graph` invocations must have started at approximately the same time (concurrent execution).
*   The `integration_graph` invocation must have occurred *after* both `coder_graph` invocations completed.
*   The `qa_graph` invocation must have occurred *after* the `integration_graph` invocation completed.
*   The method must execute to completion without throwing exceptions.

### Scenario ID: UAT-05-02 (Priority: Medium)
**Description:** Verify that a catastrophic failure in any single Phase 2 Coder cycle halts the entire pipeline, preventing corrupted code from entering the Integration or QA phases.
**Setup:** A Marimo notebook executing `WorkflowService.run_full_pipeline` with a simulated failure in one concurrent branch.
**Execution (Mock Mode):**
*   Initialize `WorkflowService` and mock its `GraphBuilder` instance.
*   Mock `build_coder_graph().ainvoke` to return success for Cycle 1 and raise an `Exception` (or return an error state) for Cycle 2.
*   Execute `run_full_pipeline()`.
**Verification:**
*   The method must catch the exception and execute `sys.exit(1)`.
*   The `integration_graph` and `qa_graph` must **never** be invoked.

## Behavior Definitions

**Feature:** Global Pipeline Orchestration
**As a** system orchestrator,
**I want** to execute all required development cycles concurrently, wait for their completion, integrate their branches natively via 3-way diffs, and validate the resulting system,
**So that** I can confidently deploy fully autonomous AI-generated features without human intervention or premature validation.

**Scenario:** Successful 5-Phase Pipeline Execution
**GIVEN** an initialized project session with a generated `CycleManifest` containing multiple feature definitions
**WHEN** the user executes the `run-pipeline` command
**THEN** the system must invoke all Phase 2 Coder Graphs concurrently
**AND** upon complete success of all parallel nodes, it must transition smoothly to Phase 3 Integration
**AND** upon resolving all integration conflicts, it must transition to Phase 4 QA
**AND** complete successfully, emitting a finalized Pull Request url.

**Scenario:** Early Pipeline Halting on Coder Failure
**GIVEN** an active global execution where Phase 2 Coder graphs are running concurrently
**WHEN** one of the Coder cycles encounters a permanent failure (e.g., maximum refactor retries reached, or syntax evaluation continuously fails)
**THEN** the orchestrator must instantly halt the pipeline
**AND** block any transition to Phase 3 Integration or Phase 4 QA.