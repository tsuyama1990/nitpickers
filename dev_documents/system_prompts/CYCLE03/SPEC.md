# CYCLE 03 Specification: Integration Graph and Conflict Manager

## Summary
CYCLE 03 establishes the Integration Phase (Phase 3) by completely overhauling the conflict resolution logic in `src/services/conflict_manager.py` and implementing a new Integration Graph (`_create_integration_graph`) in `src/graph.py` that utilizes `IntegrationState`. This ensures all parallel coding cycles are safely merged into a central integration branch via a 3-Way Diff LLM strategy before full system testing.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
- No new external APIs. Existing `JULES_API_KEY` is heavily utilized by the `master_integrator_node`.

### B. System Configurations (`docker-compose.yml`)
- No structural changes to `docker-compose.yml`.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
- **Mandate Mocking:** The 3-Way Diff tests MUST mock local git operations to prevent modifying actual project history during CI runs. Use Pytest fixtures (`tmp_path`) to initialize a bare Git repository for testing the `ConflictManager` safely.
- LLM calls within `master_integrator_node` MUST be strictly mocked.

## System Architecture

```text
src/
├── **services/conflict_manager.py**  # 3-Way Diff conflict extraction logic
├── **graph.py**                      # _create_integration_graph implementation
tests/
├── **test_conflict_manager.py**      # Unit tests for Git 3-Way Diff logic
├── **test_integration_graph.py**     # Graph traversal tests
```

## Design Architecture

### `src/services/conflict_manager.py`
The `ConflictManager` is responsible for generating the prompt payload for the `master_integrator_node`. It interacts with the local git repository to extract the historical states of a conflicted file.

1.  **`scan_conflicts()`:**
    -   **Logic:** Executes `git diff --name-only --diff-filter=U` to identify files in a conflicted state.

2.  **`build_conflict_package(file_path: str)` (Refactor):**
    -   **Concept:** Instead of just sending a file with `<<<<<<<` markers, we send the Base, Local, and Remote file contents individually.
    -   **Git Commands:**
        -   Base code (`:1`): `git show :1:{file_path}`
        -   Local code (`:2`): `git show :2:{file_path}`
        -   Remote code (`:3`): `git show :3:{file_path}`
    -   **Prompt Construction:** The method constructs a strict prompt string:
        ```markdown
        あなた（Master Integrator）の任務は、Gitのコンフリクトを安全に解消することです。
        以下の共通祖先（Base）のコードに対して、Branch AとBranch Bの変更意図を両立させた、最終的な完全なコードを生成してください。

        ### Base (元のコード)
        ```python
        {base_code}
        ```

        ### Branch A の変更 (Local)
        ```python
        {local_code}
        ```

        ### Branch B の変更 (Remote)
        ```python
        {remote_code}
        ```
        ```

### `src/graph.py` (`_create_integration_graph`)
A new LangGraph executing under Phase 3.

1.  **Nodes:**
    -   `git_merge_node`: Attempts a standard `git merge <branch>`. If successful, sets state to "success". If conflicted, sets state to "conflict".
    -   `master_integrator_node`: Uses `ConflictManager` to build the prompt, invokes Jules LLM, and writes the resolved file back to disk, then stages it (`git add`).
    -   `global_sandbox_node`: Runs global Ruff and Pytest against the entire project.
2.  **Edges:**
    -   `START` -> `git_merge_node`
    -   `git_merge_node` -> Conditional (`route_merge`) -> "conflict" (`master_integrator_node`) or "success" (`global_sandbox_node`)
    -   `master_integrator_node` -> `git_merge_node` (retry merge)
    -   `global_sandbox_node` -> Conditional (`route_global_sandbox`) -> "failed" (`master_integrator_node` as fixer) or "pass" (`END`)

## Implementation Approach

1.  **Refactor `ConflictManager`:**
    -   Open `src/services/conflict_manager.py`.
    -   Implement the Git subprocess calls in `build_conflict_package` to extract the three states.
    -   Format the precise prompt payload.

2.  **Implement `_create_integration_graph`:**
    -   Open `src/graph.py`.
    -   Wire the `IntegrationState` to the graph definition.
    -   Implement the new routing logic specific to integration (e.g., handling global sandbox failures).

3.  **Update Routing Logic:**
    -   In `src/nodes/routers.py`, add `route_merge` and `route_global_sandbox` functions.

## Test Strategy

### Unit Testing Approach
-   **File:** `tests/test_conflict_manager.py`
-   **Objectives:**
    -   **DB Rollback Rule:** Initialize a real temporary git repository using `tmp_path`, create a base commit, create two diverging branches, and merge them to deliberately cause a conflict.
    -   Execute `build_conflict_package` against this temporary repo and assert that the prompt contains the three distinct file versions correctly without failure.

### Integration Testing Approach
-   **File:** `tests/test_integration_graph.py`
-   **Objectives:** Mock the LLM and the Git commands, traverse the `IntegrationState` from `git_merge_node` through a simulated conflict, resolution, and successful `global_sandbox_node` pass.