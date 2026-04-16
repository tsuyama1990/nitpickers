# CYCLE04: User Acceptance Testing

## Test Scenarios

### SCENARIO-04-01: Independent QA Graph Execution
- **Priority**: High
- **Description**: Verify the UAT & QA Graph runs successfully in an isolated environment post-integration.

## Behavior Definitions

```gherkin
FEATURE: Decoupled UAT Execution

  SCENARIO: QA Graph remediation loop
    GIVEN the Phase 3 integration is complete
    WHEN the QA Graph is executed
    AND a simulated Playwright test fails
    THEN the `qa_auditor` MUST diagnose the failure
    AND the `qa_session` MUST attempt a fix
    AND the loop MUST repeat until the `uat_evaluate` node passes
```