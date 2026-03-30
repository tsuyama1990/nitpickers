# CYCLE 03: Phase 3 Integration Graph UAT

## Test Scenarios

### Scenario ID: UAT-03-01 (Priority: High)
**Description:** Verify the `master_integrator_node` successfully generates and resolves a 3-way diff package when encountering a simulated Git merge conflict.
**Setup:** A Marimo notebook executing the `_create_integration_graph` using `pytest.MonkeyPatch` to simulate deterministic node responses and a predefined `IntegrationState` containing unresolved conflicts.
**Execution (Mock Mode):**
*   Initialize `IntegrationState` with a simulated conflict registry.
*   Execute the compiled `integration_graph`.
*   Mock `git_merge_node` to return `status="conflict"` on the first run, and `status="success"` on the second.
*   Mock `master_integrator_node` to accept the 3-way diff package and return a unified code block.
*   Mock `global_sandbox_node` to return an "approve" result.
**Verification:**
*   The `git_merge_node` must have been visited twice.
*   The `master_integrator_node` must have been visited exactly once.
*   The `global_sandbox_node` must have been visited exactly once, terminating the graph successfully.

### Scenario ID: UAT-03-02 (Priority: Medium)
**Description:** Verify the `ConflictManager` correctly parses Git output (`git show :1`, `:2`, `:3`) into a well-structured LLM prompt containing the Base, Local, and Remote code.
**Setup:** A Marimo notebook block directly instantiating the `ConflictManager` and overriding its internal subprocess runner.
**Execution (Mock Mode):**
*   Instantiate `ConflictManager` with a mocked `ProcessRunner`.
*   Configure the mock runner to return predefined string literals for `:1`, `:2`, and `:3` commands.
*   Invoke `build_conflict_package(file_path)`.
**Verification:**
*   The generated prompt string must contain explicit headers (e.g., `### Base`, `### Branch A`, `### Branch B`).
*   The prompt must accurately embed the exact string literals provided by the mocked runner under their respective headers.

## Behavior Definitions

**Feature:** 3-Way Diff Integration Resolution
**As a** system orchestrator,
**I want** to resolve Git merge conflicts autonomously using the common ancestor, local, and remote file versions,
**So that** I can intelligently merge parallel feature branches without human intervention and without confusing the LLM with inline conflict markers.

**Scenario:** Successful 3-Way Merge resolution
**GIVEN** an active Integration Phase where `git merge` has failed with conflicts
**WHEN** the pipeline routes to the `master_integrator_node`
**AND** the `ConflictManager` fetches the base, local, and remote versions
**THEN** a structured prompt containing all three versions must be generated
**AND** upon successful generation of unified code, the pipeline must attempt `git_merge_node` again.

**Scenario:** Clean Integration Path
**GIVEN** an active Integration Phase where all feature branches cleanly merge
**WHEN** the initial `git_merge_node` executes
**THEN** the pipeline must bypass the `master_integrator_node` entirely
**AND** immediately route to the `global_sandbox_node` for final system validation.