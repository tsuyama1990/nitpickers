# CYCLE02 UAT Plan

## Test Scenarios

### ID: UAT-C02-001 (Priority: High)
- **Title**: Verify Phase 2 (Coder) Graph Instantiation and Edge Topology
- **Description**: Ensure `GraphBuilder._create_coder_graph` physically constructs a `StateGraph` containing exactly the nodes (`coder_session`, `self_critic`, `sandbox_evaluate`, `auditor_node`, `refactor_node`, `final_critic_node`) and edges specified by the 5-Phase architecture.
- **Why**: This validates the core sequential loop architecture and ensures the router functions from CYCLE01 are correctly wired into the graph's conditional edges.

### ID: UAT-C02-002 (Priority: High)
- **Title**: Verify Phase 3 (Integration) Graph Instantiation and Edge Topology
- **Description**: Ensure `GraphBuilder._create_integration_graph` constructs the new graph containing `git_merge_node`, `master_integrator_node`, and `global_sandbox_node`, with the correct conditional routing back to `git_merge_node` upon conflict.
- **Why**: This proves the integration phase is successfully modeled as a distinct, iterable state machine capable of self-healing merge conflicts.

### ID: UAT-C02-003 (Priority: Critical)
- **Title**: Verify Full Pipeline Orchestration Sequence
- **Description**: Ensure `WorkflowService.run_pipeline` (or equivalent) successfully executes multiple Phase 2 Coder graphs concurrently, waits for their completion, executes the Phase 3 Integration graph, and finally executes the Phase 4 QA graph.
- **Why**: This is the ultimate E2E test of the 5-Phase architecture's orchestration, proving the phases run in the exact order required to guarantee zero-trust integration.

### ID: UAT-C02-004 (Priority: High)
- **Title**: Verify Pipeline Orchestration Halts on Coder Failure
- **Description**: Ensure `WorkflowService.run_pipeline` aborts the Integration and QA phases if one or more of the parallel Phase 2 Coder graphs fail (e.g., maximum audit rejections reached).
- **Why**: This validates the zero-trust gatekeeping: flawed feature branches must never reach the integration phase.

## Behavior Definitions

```gherkin
Feature: 5-Phase Graph Orchestration
  As the Workflow Orchestrator
  I want the StateGraphs to be physically wired according to the specification
  So that the execution flow seamlessly transitions between phases

  Scenario: Coder Graph topological integrity
    Given the GraphBuilder is initialized
    When "_create_coder_graph" is called
    Then the resulting graph should contain the node "auditor_node"
    And it should contain a conditional edge originating from "sandbox_evaluate"
    And it should contain a conditional edge originating from "auditor_node"

  Scenario: Integration Graph topological integrity
    Given the GraphBuilder is initialized
    When "_create_integration_graph" is called
    Then the resulting graph should contain the node "git_merge_node"
    And it should contain a conditional edge originating from "git_merge_node" routing to "master_integrator_node" on conflict

  Scenario: Full Pipeline Sequential Execution
    Given the WorkflowService is initialized with two pending cycles
    And the Coder, Integration, and QA graphs are mocked to succeed
    When "run_pipeline" is called
    Then it should execute the Coder graph twice concurrently
    And upon completion, it should execute the Integration graph exactly once
    And upon completion, it should execute the QA graph exactly once

  Scenario: Full Pipeline aborts on Coder failure
    Given the WorkflowService is initialized with two pending cycles
    And the first Coder graph is mocked to succeed
    But the second Coder graph is mocked to fail (e.g., reject status)
    When "run_pipeline" is called
    Then it should execute both Coder graphs concurrently
    And it should NOT execute the Integration graph
    And it should NOT execute the QA graph
    And it should raise or return a failure status
```