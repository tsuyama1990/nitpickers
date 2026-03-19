# CYCLE 06 UAT: Conflict Extraction & Registry Management

## Test Scenarios
- **Scenario ID 06-01:** Successful Clean Merge
  - Priority: Medium
  - When two non-overlapping branches are merged, `safe_merge_with_conflicts` completes successfully without triggering the ConflictManager.
  - Validates baseline git functionality is not broken.

- **Scenario ID 06-02:** Conflict Extraction and Registration
  - Priority: Critical
  - When two branches modify the same line, the merge must fail but the files must retain the standard Git conflict markers (`<<<<<<< HEAD`, etc.).
  - The `ConflictManager` must extract the conflicted files and store them in the project manifest's `ConflictRegistry`.

- **Scenario ID 06-03:** Resolution Validation Failsafe
  - Priority: High
  - If a file still contains conflict markers, the `validate_resolution` method must prevent any subsequent `git commit` or integration step. It must explicitly block progress.
  - This guarantees hallucinated or incomplete AI resolutions do not corrupt the codebase.

## Behavior Definitions
- **GIVEN** a local branch `feature/A` and `main` with non-conflicting changes
  **WHEN** `safe_merge_with_conflicts` is called
  **THEN** the merge succeeds (returns `True`) and the `ConflictRegistry` remains empty.

- **GIVEN** a local branch `feature/B` that modifies line 10 to "X" and `main` that modified line 10 to "Y"
  **WHEN** `safe_merge_with_conflicts` is called
  **THEN** the merge fails (returns `False`), but the file retains the `<<<<<<<` markers.
  **AND** the `ConflictManager.scan_conflicts` method returns a populated `ConflictRegistryItem` for that file.

- **GIVEN** a `ConflictRegistryItem` pointing to a conflicted file
  **WHEN** `validate_resolution` is called on the file containing markers
  **THEN** the function returns `False` and a `ConflictMarkerRemainsError` is raised before committing.

- **GIVEN** the same file where the markers have been completely replaced with unified logic
  **WHEN** `validate_resolution` is called
  **THEN** the function returns `True` and the commit process is allowed to proceed.
