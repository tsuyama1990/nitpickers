# CYCLE 05 UAT: Red Team Auditor & Intra-Cycle Refactor

## Test Scenarios
- **Scenario ID 05-01:** Red Team Rejection Loop
  - Priority: Critical
  - Code that functionally passes E2B tests but contains a logical vulnerability (e.g., hardcoded mock secret) must be caught by the Auditor using the `CODER_CRITIC_INSTRUCTION` and sent back for a rewrite.
  - This proves that dynamic success alone is insufficient.

- **Scenario ID 05-02:** Auditor Approval & Post-Audit Refactor Suggestion
  - Priority: High
  - If the code passes the Auditor, but the `coder_critic_node` (using `POST_AUDIT_REFACTOR_INSTRUCTION`) identifies a McCabe complexity > 10, the cycle must retry the Coder phase for refactoring.
  - This validates the evolutionary code improvement constraint.

- **Scenario ID 05-03:** Final Approval
  - Priority: Medium
  - When the code is perfectly structured, passes E2B, passes the Auditor, and requires no refactoring, the pipeline must route to `COMPLETED`.

## Behavior Definitions
- **GIVEN** a working but vulnerable implementation (e.g., SQL Injection risk)
  **WHEN** the `auditor_node` reviews the code against the `CODER_CRITIC_INSTRUCTION.md`
  **THEN** the auditor returns `is_approved=False` with the vulnerability detailed, and the orchestrator routes the cycle back to the `coder_session_node`.

- **GIVEN** a secure, functional implementation with poorly named variables and long methods
  **WHEN** the code reaches the `coder_critic_node`
  **THEN** the Coder's Self-Critic responds with refactoring suggestions, the node sets `status = CODER_RETRY`, and the Coder rewrites the methods.

- **GIVEN** a clean, secure, simple implementation
  **WHEN** it is processed by the `auditor_node` and `coder_critic_node`
  **THEN** both nodes approve it, the `committee_manager` marks it `READY_FOR_MERGE`, and the LangGraph execution finishes successfully.