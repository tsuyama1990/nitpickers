# CYCLE 06 Specification: Conflict Extraction & Registry Management

## Summary
The goal of CYCLE 06 is to implement the "Cascading Merge Resolutions" concept. When multiple concurrent cycles (e.g., 01, 02, 03) complete and attempt to merge into the integration branch, Git conflicts are inevitable. Instead of aborting the merge or failing the pipeline, the `ConflictManager` will perform a `git merge --no-commit --no-ff`. It will intentionally preserve the Git conflict markers (`<<<<<<< HEAD`, `=======`, `>>>>>>>`). It then extracts these conflicted files and logs them into a `ConflictRegistry` stored in the LangGraph state. This registry acts as the bookkeeper to ensure no conflict marker is hallucinated away or ignored by the AI in the next cycle.

## System Architecture
This cycle involves creating the `ConflictManager` service and modifying `git_ops.py` to support non-aborting merges.

### File Structure Blueprint
```text
/
├── pyproject.toml
├── src/
│   ├── git_ops.py               (Update: Add safe_merge_with_conflicts method)
│   ├── workflow.py              (Update: Post-cycle merge logic)
│   └── services/
│       └── conflict_manager.py  (New: Extracts and validates conflict markers)
└── tests/
    └── unit/
        ├── test_git_ops.py      (Update)
        └── test_conflict.py     (New)
```
**Modifications:**
- **`src/git_ops.py`**: Add `safe_merge_with_conflicts(branch_name)`. It returns `True` if successful, `False` if conflicts exist, but crucially, it does *not* run `git merge --abort`.
- **`src/services/conflict_manager.py`**: A new service. It scans the repository for `<<<<<<< HEAD` using a regex, creates `ConflictRegistryItem` objects for each file, and returns a list.
- **`src/workflow.py`**: In the post-cycle loop, if `safe_merge_with_conflicts` is `False`, it calls `conflict_manager` and updates the `CycleState` (or a new `IntegrationState`).

## Design Architecture
### Pydantic Models & Extensibility
1. **`ConflictManager` Interface:**
   - Methods: `def scan_conflicts(repo_path: Path) -> list[ConflictRegistryItem]`, `def validate_resolution(file_path: Path) -> bool`.
   - Dependencies: `os`, `re`, `pathlib`.
2. **Regex Parsing:**
   - Must strictly match standard Git markers: `^<{7}\s.*$`, `^={7}$`, `^>{7}\s.*$`.
   - Must capture the conflicting blocks to package them as context for the Master Integrator in Cycle 07.

### Operational Constraints
The system must never commit a file containing raw Git conflict markers. The `validate_resolution` method must be physically called before any `git commit` is permitted on the integration branch. If markers remain, the system physically throws a `ConflictMarkerRemainsError` to trigger a fail-safe.

## Implementation Approach
1. **Git Operations Update:** In `src/git_ops.py`, write `safe_merge_with_conflicts`. Use `subprocess.run` with `capture_output=True`. Check the return code. If non-zero (conflict), leave the working tree dirty.
2. **Conflict Manager Service:** In `src/services/conflict_manager.py`, implement `scan_conflicts()`. Use `git status --porcelain` or `git diff --name-only --diff-filter=U` to find unmerged files quickly, then parse them to build the registry items.
3. **Validation Mechanism:** Implement `validate_resolution()`. It reads the file and returns `False` if the regex matches any markers.
4. **Integration into Workflow:** In `src/workflow.py` (or a dedicated integration node), after a cycle is `COMPLETED`, attempt the merge. If it conflicts, call `scan_conflicts()` and save the registry to the project state JSON file to persist across sessions.

## Test Strategy
### Unit Testing Approach
- Develop `test_conflict.py`. Create a temporary file containing hardcoded Git conflict markers. Pass it to `ConflictManager.scan_conflicts()` and assert it correctly identifies the file, the number of conflict blocks, and the exact lines.
- Pass a clean file to `validate_resolution()` and assert it returns `True`. Pass the conflicted file and assert it returns `False`.

### Integration Testing Approach
- In `test_git_ops.py`, simulate two branches touching the same line of a file. Call `safe_merge_with_conflicts()`. Assert that the function returns `False` (conflict), but that the file exists on disk with the markers intact (not aborted).
- Clean up the repository state after the test to ensure side-effects don't pollute other tests.