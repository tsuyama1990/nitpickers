# CYCLE 07 Specification: Stateful Master Integrator Session

## Summary
The objective of CYCLE 07 is to implement the "Stateful Integrator Session." When CYCLE 06 detects Git conflicts, they must be resolved intelligently. Instead of spawning a new AI session for each conflict—which loses context and risks rate limits—a single, long-lived Jules session (the "Master Integrator") will be instantiated. This session receives conflict packages (the files with markers, plus context from the original specs) and is instructed to perform semantic merges, resolving markers while improving code quality. It iteratively processes the `ConflictRegistry` until all files pass the `validate_resolution` check.

## System Architecture
This cycle introduces a new dedicated LangGraph workflow or an extension of the existing integration phase, primarily updating `src/workflow.py` and `src/services/integration_usecase.py`.

### File Structure Blueprint
```text
/
├── pyproject.toml
├── src/
│   ├── workflow.py                    (Update: Implement post-cycle Integrator loop)
│   ├── graph.py                       (Update: Optional Integration Graph)
│   └── services/
│       ├── integration_usecase.py     (New: Manages Master Integrator Session)
│       └── conflict_manager.py        (Update: Build context package for Jules)
└── dev_documents/
    └── system_prompts/
        └── MASTER_INTEGRATOR_PROMPT.md (New: Fixed prompt for resolving conflicts)
```
**Modifications:**
- **`src/services/integration_usecase.py`**: A new usecase that initializes one Jules session (`IntegrationState.jules_session_id`) and sends consecutive conflict resolution requests.
- **`src/services/conflict_manager.py`**: Add `build_conflict_package(item: ConflictRegistryItem)` to format the file content and relevant `SPEC.md` fragments.
- **`src/workflow.py`**: After concurrent cycles merge and populate the `ConflictRegistry`, instantiate the Integrator and loop through the registry items.

## Design Architecture
### Pydantic Models & Extensibility
1. **`IntegrationState`:**
   - Extend the project state to track `master_integrator_session_id`.
   - Track `unresolved_conflicts: list[ConflictRegistryItem]`.
2. **Fixed Prompts:**
   - **`MASTER_INTEGRATOR_PROMPT.md`**: "You are the Master Integrator. Resolve the Git conflicts in this file. Do not just pick A or B; understand the intent of both branches. Apply DRY principles. Return the completely unified file without any `<<<<<<<` markers."

### Operational Constraints
The Master Integrator is stateful. It retains the context of previous conflict resolutions within the same session. If `validate_resolution` fails after Jules returns the code, the system immediately sends a follow-up message to the *same* session: "Your resolution failed. Conflict markers `<<<<<<<` still exist. Fix it." It must support a maximum retry limit (e.g., 3 retries per file) before aborting the merge and escalating to manual intervention.

## Implementation Approach
1. **Prompt Creation:** Write `MASTER_INTEGRATOR_PROMPT.md` prioritizing semantic merging and marker removal.
2. **Context Packaging:** In `src/services/conflict_manager.py`, implement `build_conflict_package()`. It reads the raw file with markers and (optionally) fetches the cycle IDs involved to inject their `SPEC.md` summaries for context.
3. **Integration Service:** In `src/services/integration_usecase.py`, implement the loop:
   - Check if `master_integrator_session_id` exists; if not, create it.
   - For each file in the registry, send the package via `jules.send_message_to_session()`.
   - Receive the updated code and apply it to the file.
   - Call `conflict_manager.validate_resolution()`.
   - If false, append "Markers remain!" and retry.
   - If true, mark the item `resolved=True`.
4. **Workflow Execution:** In `src/workflow.py`, once `validate_resolution` passes for all items in the registry, execute `git commit` to finalize the merge.

## Test Strategy
### Unit Testing Approach
- Develop `test_integration_usecase.py`. Mock a Jules session returning an unresolved string (containing `<<<<<<<`), assert that `validate_resolution` fails, and the loop retries.
- Mock the second response returning a clean string, assert it passes validation, applies the changes, and exits the loop.
- Assert that the `build_conflict_package()` correctly formats the prompt with the file path and content.

### Integration Testing Approach
- In `test_workflow.py`, simulate an integration phase with a populated `ConflictRegistry`. Mock the Master Integrator to sequentially "fix" two files.
- Assert that only one `run_session` (or `create_session`) is called, and subsequent calls use `send_message_to_session` with the same session ID, proving statefulness.
- Assert that a `git commit` is successfully executed at the end of the pipeline.