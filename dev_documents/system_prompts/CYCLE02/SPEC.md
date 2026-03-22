# CYCLE02 Specification: Integration Phase & 3-Way Diff Resolution

## Summary
CYCLE02 focuses on implementing the "Integration Phase" (Phase 3) of the NITPICKERS 5-phase architecture. This phase acts as a critical bottleneck where parallel, successfully audited feature branches (from Phase 2) are merged into a single integration branch. The core technical challenge addressed in this cycle is intelligent conflict resolution. Instead of relying on manual intervention or failing the build when Git encounters a merge conflict, the system will employ a Master Integrator LLM utilizing a "3-Way Diff" strategy. This approach provides the LLM with the common ancestor (Base), the Local changes, and the Remote changes, allowing it to safely synthesize a unified file that preserves the intentions of both branches.

## System Architecture
This cycle introduces a new LangGraph specifically for integration (`_create_integration_graph`) and heavily refactors the conflict management services to support the 3-Way Diff strategy.

### File Structure Modifications
The following files will be created or modified:

```text
src/
├── **state.py** (Adding/Refining IntegrationState)
├── **graph.py** (Creating _create_integration_graph)
└── services/
    └── **conflict_manager.py** (Implementing 3-Way Diff logic)
```

### Components and Interactions
1.  **Integration Graph (`src/graph.py`)**: A new LangGraph definition will orchestrate the integration process.
    -   `git_merge_node`: Attempts a standard `git merge` of a feature branch into the integration branch.
    -   `master_integrator_node`: Triggered if `git_merge_node` encounters a conflict. It invokes the LLM to resolve the conflict.
    -   `global_sandbox_node`: Runs a comprehensive suite of static checks and unit tests across the entire integrated codebase to ensure no regressions were introduced during the merge.
2.  **Conflict Manager (`src/services/conflict_manager.py`)**: This service is the heart of the intelligent resolution process. It must be refactored to extract the three distinct versions of a conflicted file from Git history.
    -   `build_conflict_package`: A new or heavily modified method that uses Git commands (e.g., `git show :1:{file}`, `:2:{file}`, `:3:{file}`) to retrieve the Base, Local, and Remote file contents. It then formats these into a structured prompt for the Master Integrator LLM.
3.  **State Management (`src/state.py`)**: The `IntegrationState` model will be formalized to track the list of feature branches pending merge, the current active branch, and any unresolved `ConflictRegistryItem` objects.

## Design Architecture
The Integration Phase relies on strict state boundaries to ensure that parallel development streams do not corrupt each other during the merge process.

### Domain Concepts
-   **IntegrationState**: A Pydantic model tracking the overall progress of Phase 3. It manages a queue of branches to merge and holds the results of the global sandbox evaluation.
-   **ConflictRegistryItem**: An existing (or to-be-refined) model that represents a single conflicted file. It must be updated to store or reference the Base, Local, and Remote code strings, in addition to the file path.
-   **3-Way Diff Package**: A structured payload sent to the LLM. It is not just a diff with `<<<<<<<` markers; it presents the three complete versions of the code to provide maximum context.
-   **ConflictResolutionSchema**: A strictly defined Pydantic model that the Master Integrator LLM must return. This ensures the output is always a JSON object containing the `resolved_code` string, eliminating fragile markdown regex extraction entirely.

### Invariants and Constraints
-   The Integration Phase *must not* begin until all active Coder Phase (Phase 2) graphs have reached the `END` state successfully.
-   The `master_integrator_node` must output syntactically valid code, enforced via the `ConflictResolutionSchema`. It cannot output code containing Git conflict markers.
-   The `build_conflict_package` must use `try/except` blocks to handle Git failures (e.g., when a file is newly created in Branch A, Git will fail to find it in the Base commit). It must inject explicit string markers like `<FILE_NOT_IN_BASE>` instead of crashing.
-   If the `global_sandbox_node` fails after a merge, the system must route back to a diagnostic or integration-fix node (or fail fast depending on configuration), as this indicates a semantic conflict that Git and the Integrator missed.

### Extensibility and Backward Compatibility
The `conflict_manager.py` service will retain its existing interface where possible, but internal methods like `scan_conflicts` will be augmented to utilize the new 3-Way Diff data extraction. Existing tests that expect raw conflict marker strings will need to be updated to expect the new structured prompt payload.

## Implementation Approach
The implementation will focus on safe Git operations and robust prompt engineering for the Master Integrator.

1.  **Refine `IntegrationState` (`src/state.py`)**:
    -   Ensure `IntegrationState` includes fields for tracking merge attempts and sandbox results.
    -   Verify `ConflictRegistryItem` can hold the necessary file path data.

2.  **Implement 3-Way Diff Logic (`src/services/conflict_manager.py`)**:
    -   Locate or create the `build_conflict_package` method.
    -   Utilize `ProcessRunner` or a similar safe subprocess execution mechanism to run:
        -   `git show :1:{filepath}` (Base)
        -   `git show :2:{filepath}` (Local/Current Branch)
        -   `git show :3:{filepath}` (Remote/Merging Branch)
    -   Handle cases where a file might be newly added in one branch and thus missing a Base (returns empty string or specific marker).
    -   Construct the prompt string strictly adhering to the format specified in `ALL_SPEC.md` (sections for `### Base`, `### Branch A`, `### Branch B`).

3.  **Construct `_create_integration_graph` (`src/graph.py`)**:
    -   Define the nodes: `git_merge_node`, `master_integrator_node`, `global_sandbox_node`.
    -   Define the edges:
        -   `START` $\rightarrow$ `git_merge_node`
        -   `git_merge_node` $\rightarrow$ conditional route (`"conflict"` $\rightarrow$ `master_integrator_node`, `"success"` $\rightarrow$ `global_sandbox_node`)
        -   `master_integrator_node` $\rightarrow$ `git_merge_node` (to retry the merge or commit the resolution)
        -   `global_sandbox_node` $\rightarrow$ conditional route (`"failed"` $\rightarrow$ `master_integrator_node` (or dedicated fix node), `"pass"` $\rightarrow$ `END`)

## Test Strategy

### Unit Testing Approach (Min 300 words)
The unit testing for CYCLE02 will heavily target the `ConflictManager` service to ensure it correctly interacts with Git and formats the LLM prompts accurately without relying on live Git repositories.

In `tests/services/test_conflict_manager.py`, we will use the `unittest.mock` library to patch the `ProcessRunner.run_command` method. When `build_conflict_package` calls Git to retrieve file versions, the mock will intercept these calls and return predefined strings representing the Base, Local, and Remote code. We will assert that the resulting prompt string exactly matches the expected markdown structure containing the three code blocks.

Furthermore, we must write tests to handle edge cases. What if a file was created in Branch A but modified in Branch B, meaning there is no "Base" version in the common ancestor? The mock will return an empty string or a non-zero exit code for `git show :1:...`, and we will assert that the `ConflictManager` handles this gracefully, perhaps indicating "New File" in the Base section of the prompt. By isolating the Git subprocess calls, these unit tests will run blazingly fast and provide deterministic proof that the core logic of the 3-Way Diff data gathering is flawless.

### Integration Testing Approach (Min 300 words)
Integration testing for Phase 3 requires simulating a realistic Git merge scenario and verifying the LangGraph routing logic. This will be implemented in `tests/test_integration_graph.py`.

Unlike unit tests, these integration tests will utilize a temporary directory fixture containing an actual, isolated Git repository. We will programmatically create a base commit, branch off two parallel feature branches, and make conflicting modifications to the same file. We will then invoke the `_create_integration_graph`.

We will mock the LLM call inside `master_integrator_node` to return a predefined, correctly merged code string. The test will verify the following sequence: The graph starts, `git_merge_node` attempts the merge and correctly detects a conflict (routing to `"conflict"`). The `master_integrator_node` is invoked, receives the correct 3-Way Diff prompt (verified via mock inspection), and applies the mocked resolution. The graph then routes back to `git_merge_node` (which now succeeds) or directly to `global_sandbox_node`. We will verify that the global sandbox executes and, upon success, the graph reaches the `END` state. This end-to-end integration test proves that the LangGraph orchestrator and the underlying Git operations work together seamlessly to automate conflict resolution.