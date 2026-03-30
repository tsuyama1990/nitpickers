# CYCLE04 UAT Plan

## Test Scenarios

### Scenario 1: End-to-End Orchestration Execution (Priority: Critical)
This scenario ensures that the CLI entry point correctly orchestrates Phase 1, Phase 2 (concurrent execution), Phase 3 (sequential integration), and Phase 4 (UAT) as defined by the new 5-Phase Architecture.

### Scenario 2: Orchestrator Failure Handling (Priority: High)
This scenario ensures the Orchestrator correctly halts execution and reports an overall failure if any parallel Coder iteration exceeds retry limits or if Integration fails catastrophically.

### Behavior Definitions

**Scenario 1: End-to-End Orchestration Execution**

GIVEN a valid `ALL_SPEC.md`
WHEN the `run_pipeline` CLI command is executed
THEN the system should concurrently execute the specified `CycleState` instances in Phase 2
AND wait for their completion
AND successfully transition to the `_create_integration_graph` in Phase 3
AND subsequently execute the `_create_qa_graph` in Phase 4
AND the command should complete with a zero exit code

**Scenario 2: Orchestrator Failure Handling**

GIVEN a valid `ALL_SPEC.md`
WHEN the `run_pipeline` CLI command is executed
AND a Phase 2 Coder cycle encounters a critical, unrecoverable error during sandbox evaluation
THEN the Orchestrator should halt further progression
AND the Phase 3 `_create_integration_graph` should NOT be initiated
AND the command should return a non-zero exit code indicating the specific failure
