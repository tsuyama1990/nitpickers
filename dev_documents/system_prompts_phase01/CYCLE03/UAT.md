# UAT: Cycle 03 - Red Teaming Intra-cycle & Linter Enforcement

## Test Scenarios

### Scenario ID: UAT-C03-001 - Strict Linter Rejection Loop
**Priority**: High
**Description**: This scenario verifies that the mechanical static analysis gate correctly identifies and rejects syntactically flawed code before any LLM auditing occurs. We will utilize a Marimo notebook to inject a Python file with a deliberate, severe type mismatch (violating strict `mypy` rules) into the workflow. The test will monitor the LangGraph state transitions to ensure the `linter_gate_node` immediately catches the error, halts forward progress, and routes the raw error output back to the Coder session for an immediate fix.

### Scenario ID: UAT-C03-002 - Coder Critic Logical Review
**Priority**: Medium
**Description**: This scenario tests the `CoderCritic` node's ability to identify logical flaws that linters miss. We will provide syntactically perfect code that nevertheless contains a hardcoded API key or an obvious N+1 query pattern. The test will verify that the prompt-driven Red Team evaluation correctly flags these anti-patterns based on the predefined checklist and forces the AI to refactor the code before it is allowed to proceed to the UAT sandbox phase.

## Behavior Definitions

```gherkin
Feature: Intra-cycle Red Teaming and Static Analysis
  As an AI Orchestrator
  I want to strictly validate generated code using deterministic linters and rigorous self-critique
  So that I prevent flawed or sloppy code from wasting resources in the dynamic testing sandbox

  Scenario: The Linter Gate rejects code with a strict type mismatch
    Given the Coder session has generated a Python file
    And the file contains a deliberate type error (e.g., assigning a string to an int hint)
    When the workflow transitions to the Linter Gate node
    Then the static analysis execution (mypy) must return a non-zero exit code
    And the workflow must be blocked from proceeding to the Sandbox UAT
    And the raw mypy error output must be routed back to the Coder session for correction

  Scenario: The Coder Critic node flags a hardcoded variable
    Given the code has successfully passed the Linter Gate
    And the code contains a hardcoded 'localhost:8080' string instead of an environment variable
    When the workflow transitions to the Coder Critic node
    Then the evaluation against the strict checklist must detect the hardcoded value
    And the system state must update with the specific refactoring requirement
    And the workflow must route back to the Coder session to remove the hardcoded string
```
