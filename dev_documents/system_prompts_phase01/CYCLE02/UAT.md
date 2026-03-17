# UAT: Cycle 02 - Concurrent Dispatcher & Workflow Modification

## Test Scenarios

### Scenario ID: UAT-C02-001 - Massive Throughput Validation
**Priority**: High
**Description**: This scenario verifies the core value proposition: parallel execution. We will construct a project manifest with 3 independent cycles. We will mock the LLM execution to take exactly 3 seconds per cycle. If the asynchronous dispatcher is functioning correctly, the total execution time for all 3 cycles should be slightly over 3 seconds, not 9 seconds. The test will run via a Marimo notebook, visually demonstrating the overlapping execution timelines and proving the Massive Throughput capability.

### Scenario ID: UAT-C02-002 - Resilience against API Rate Limits (429)
**Priority**: Medium
**Description**: This scenario tests the safety nets required for concurrent requests. We will simulate a scenario where blasting multiple LLM requests triggers an HTTP 429 Too Many Requests response from the mocked API provider. The system must autonomously catch this specific error, apply an exponential backoff with jitter, and safely retry the request without failing the graph execution or crashing the orchestrator.

## Behavior Definitions

```gherkin
Feature: Concurrent Cycle Execution and Resilience
  As an AI Orchestrator
  I want to dispatch multiple development cycles asynchronously
  So that I can drastically reduce the overall project completion time

  Scenario: Dispatching multiple independent cycles concurrently
    Given a project manifest containing 3 pending, independent cycles
    And the LLM execution is mocked to take 3 seconds per cycle
    When the workflow service initiates the run-cycle command for all pending cycles
    Then the asynchronous dispatcher must launch 3 parallel tasks
    And the total execution time must be less than 5 seconds
    And the state for all 3 cycles must be marked as COMPLETED

  Scenario: Recovering from HTTP 429 Too Many Requests during concurrent bursts
    Given the asynchronous dispatcher is launching multiple cycles
    And the API provider returns an HTTP 429 error for one of the concurrent requests
    When the request fails
    Then the network layer must intercept the 429 error
    And it must apply an exponential backoff delay
    And it must successfully retry the request
    And the overall workflow must not crash or exit prematurely
```
