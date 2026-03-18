# CYCLE 08 Specification: Global Refactor Node & Final Stabilization

## Summary
The goal of CYCLE 08 is to perform the "Overall Refactor." After all concurrent cycles have been successfully implemented and integrated (and conflicts semantically resolved in Cycle 07), the entire codebase must be reviewed. Because cycles were developed in silos, there is a high likelihood of duplicate utility functions, inconsistent error handling, or minor structural drift. This final LangGraph node analyzes the complete Abstract Syntax Tree (AST) against the initial `SYSTEM_ARCHITECTURE.md` to identify global DRY violations and apply project-wide optimizations. It acts as the final "Abundance Recovery" mechanism before submitting a production-ready PR.

## System Architecture
This cycle involves adding a `global_refactor_node` to the workflow post-integration and integrating the final, stringent Linter and UAT validation steps to guarantee stability.

### File Structure Blueprint
```text
/
├── pyproject.toml
├── src/
│   ├── workflow.py                    (Update: Add Global Refactor to post-integration)
│   ├── nodes/
│   │   └── global_refactor.py         (New: Isolated global_refactor_node implementation)
│   └── services/
│       ├── refactor_usecase.py        (New: Analyze and apply global refactoring)
│       └── ast_analyzer.py            (New: AST parsing for duplicate logic detection)
└── dev_documents/
    └── system_prompts/
        └── GLOBAL_REFACTOR_PROMPT.md  (New: Fixed prompt for global optimization)
```
**Modifications:**
- **`src/nodes/global_refactor.py`**: Registers the node that calls the refactor usecase and validates post-refactor tests.
- **`src/services/refactor_usecase.py`**: A new service. It utilizes `ast_analyzer.py` (a Python AST parser) to detect identical or highly similar function signatures across modules. It packages this data into the `GLOBAL_REFACTOR_PROMPT.md` and sends it to the Master Integrator session.
- **`src/workflow.py`**: After the integration commit, invoke the Global Refactor node. This is followed immediately by the standard Auditor node loop (reuse from Cycle 05) to ensure the refactor didn't introduce bugs.

## Design Architecture
### Pydantic Models & Extensibility
1. **`GlobalRefactorResult`:**
   - Properties: `refactorings_applied` (bool), `modified_files` (list[str]), `summary` (str).
2. **Fixed Prompts:**
   - **`GLOBAL_REFACTOR_PROMPT.md`**: "Analyze the complete project context. Unify duplicated logic across the following modules: {AST_duplicates}. Ensure consistent error handling and typing. Ensure maximum McCabe complexity is strictly under 10. Do not break existing tests."

### Final Pre-commit Enforcement
This node is the last stage before `finalize-session`. After the global refactor, the system *must* re-run `ruff check .`, `ruff format .`, `mypy --strict .`, and the full E2B UAT test suite (`pytest`). Only if all tests remain "Green" can the final PR be generated.

## Implementation Approach
1. **AST Analysis:** In `src/services/ast_analyzer.py`, use Python's built-in `ast` module to scan `src/` for function definitions (`ast.FunctionDef`). Hash the node structure (ignoring variable names) to identify functionally identical methods created in silos.
2. **Refactor Service:** In `src/services/refactor_usecase.py`, take the AST output and package it into the `GLOBAL_REFACTOR_PROMPT.md`. Send this to the persistent Master Integrator session.
3. **Workflow Integration:** In `src/workflow.py`, append `global_refactor_node` after the conflict resolution loop.
4. **Final Quality Gates:** Ensure the `global_refactor_node` invokes the `auditor_node` and `uat_evaluate_node` (E2B Sandbox) one final time before completing the `finalize-session` process. If the refactor fails the tests, it must rollback the refactor commit or prompt Jules to fix it immediately.

## Test Strategy
### Unit Testing Approach
- Develop `test_ast_analyzer.py`. Create two identical mock Python functions in separate test files. Run `ast_analyzer.py` and assert it flags them as duplicates.
- Develop `test_refactor_usecase.py`. Mock the Jules session returning unified code. Assert that it applies the code and updates `GlobalRefactorResult.refactorings_applied = True`.

### Integration Testing Approach
- In `test_workflow.py`, simulate the final stages: Integration completes $\rightarrow$ Global Refactor invoked $\rightarrow$ Mock AST duplicate found $\rightarrow$ Mock Jules fixes it $\rightarrow$ Final `ruff/mypy/pytest` loop passes $\rightarrow$ Final PR created.
- Assert that if the final test suite fails after refactoring, the system triggers the standard Coder/Auditor retry loop to correct the regression.