# CYCLE 08 UAT: Global Refactor Node & Final Stabilization

## Test Scenarios
- **Scenario ID 08-01:** Successful Global Refactoring
  - Priority: Medium
  - When the final integration is complete, the `GlobalRefactor` node uses AST analysis to identify duplicated logic across `src/` files and prompts the Master Integrator to unify them without breaking tests.

- **Scenario ID 08-02:** Final Quality Gate Failsafe (Linter/Tests)
  - Priority: Critical
  - If the `GlobalRefactor` modifies the codebase but inadvertently causes `ruff`, `mypy`, or `pytest` to fail, the node must immediately detect this, log a regression error, and prompt the AI to revert or fix the change.
  - This ensures that "Abundance Recovery" does not compromise the project's zero-trust validation before the final PR.

- **Scenario ID 08-03:** Unmodified Clean Architecture
  - Priority: Low
  - If the `ast_analyzer` finds zero duplicated functions and the codebase already strictly adheres to DRY and complexity constraints, the `GlobalRefactor` node must return `refactorings_applied=False` and proceed to finalize without redundant LLM calls.

## Behavior Definitions
- **GIVEN** a merged codebase where `src/utils/file_A.py` and `src/utils/file_B.py` contain structurally identical functions (except for variable names)
  **WHEN** the `global_refactor_node` invokes `ast_analyzer.py`
  **THEN** the analyzer detects the duplication, passes the context to the Master Integrator session via `GLOBAL_REFACTOR_PROMPT.md`, and the AI unifies them into a single utility file.

- **GIVEN** a codebase modified by the `GlobalRefactor` node
  **WHEN** the system attempts to finalize the session
  **THEN** it first runs the `ruff check .`, `mypy --strict .`, and the E2B test suite. If any step fails (e.g., exit code > 0), the system traps the error, prevents the PR, and loops back for correction.

- **GIVEN** a highly optimized, fully DRY codebase
  **WHEN** the `global_refactor_node` scans the AST
  **THEN** no duplicates or McCabe complexity violations are found. The node logs "No global refactoring required," bypasses the Master Integrator LLM call, and proceeds to the final validation steps.