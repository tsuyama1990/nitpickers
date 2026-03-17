# UAT: Cycle 01 - Planning & Self-Critic Setup

## Test Scenarios

### Scenario ID: UAT-C01-001 - Architecture Rejection and Retry Loop
**Priority**: High
**Description**: This scenario verifies that the Self-Critic node correctly identifies deliberate architectural flaws (e.g., a missing interface contract definition in a SPEC file) and forces the Architect node into a retry loop. We will utilize a mocked LangGraph execution environment within a Marimo notebook to trace the state transitions and ensure the feedback loop operates autonomously without human intervention. The 'Magic Moment' is observing the system catch a critical flaw and self-correct its blueprint before any code is generated. This is essential for preventing costly rework downstream.

### Scenario ID: UAT-C01-002 - Successful Architecture Lock
**Priority**: High
**Description**: This scenario tests the happy path where the architecture successfully passes the rigorous checklist. We will provide a robust, flawless set of requirements to the mocked Architect. The Self-Critic node must evaluate the generated specifications, confirm that all anti-patterns are avoided and interface contracts are explicitly defined, and subsequently approve the design. The scenario concludes by verifying that the final, locked `SYSTEM_ARCHITECTURE.md` and `SPEC_cycleXX.md` files are physically written to the designated output directories.

## Behavior Definitions

```gherkin
Feature: Architectural Self-Critic Validation
  As an AI Orchestrator
  I want to automatically validate generated system architectures against strict anti-patterns
  So that I prevent flawed designs from causing failures during concurrent implementation cycles

  Scenario: The Self-Critic detects a missing interface contract and forces a retry
    Given the Architect node has generated initial specifications
    And the specifications deliberately omit function signatures in the interface definition
    When the architectural state transitions to the Self-Critic node
    Then the Self-Critic node must identify the missing contract
    And the system state must be updated to CRITIC_REJECTED
    And the workflow must route back to the Architect node with the specific feedback

  Scenario: The Self-Critic approves a robust architecture and locks the design
    Given the Architect node has generated comprehensive specifications
    And the specifications include strict interface contracts and avoid N+1 problems
    When the architectural state transitions to the Self-Critic node
    Then the Self-Critic node must approve the design
    And the system state must be updated to ARCHITECTURE_APPROVED
    And the final specification files must be written to the dev_documents directory
```
