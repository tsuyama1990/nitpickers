# UAT: Cycle 07 - Global Refactor Node

## Test Scenarios

### Scenario ID: UAT-C07-001 - Consolidation of Duplicated Logic
**Priority**: High
**Description**: This scenario verifies the system's ability to clean up the aftermath of parallel development. We will provide a pre-assembled codebase containing intentional code duplication (e.g., identical data sanitization logic appearing in two separate API handlers). The test will run the Global Refactor workflow and verify that the system correctly identifies the redundancy, extracts it into a centralized utility module, and updates all caller references. The final verification proves that the system achieved a global optimization.

### Scenario ID: UAT-C07-002 - Safety Net Validation Post-Refactor
**Priority**: High
**Description**: This scenario is critical for demonstrating the Zero-Trust safety net. We will provide a mocked LLM response for the Global Refactor node that intentionally makes a mistake (e.g., extracting a function but forgetting to update an import statement in one module). The test must verify that the subsequent automated re-validation phase immediately catches this error (either via the Linter Gate or the Sandbox UAT execution) and prevents the broken optimization from being finalized.

## Behavior Definitions

```gherkin
Feature: Post-Integration Global Optimization
  As an AI Orchestrator
  I want to perform a system-wide refactoring pass after all concurrent cycles are merged
  So that I can eliminate code duplication and ensure macro-level architectural elegance

  Scenario: The Global Refactor node consolidates duplicate helper functions
    Given all development cycles have been successfully merged
    And the codebase contains identical logic duplicated across two isolated modules
    When the workflow transitions to the Global Refactor node
    Then the system must identify the duplication
    And it must extract the shared logic into a common utility module
    And the subsequent project-wide tests must pass to confirm behavioral integrity

  Scenario: The safety net catches a breaking change during refactoring
    Given the Global Refactor node attempts an optimization
    And the optimization inadvertently breaks an existing import statement
    When the system executes the post-refactor validation pipeline
    Then the Linter Gate must immediately detect the broken import
    And the workflow must halt the finalization process
    And the error must be routed back to the refactor node for correction
```
