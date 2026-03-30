# CYCLE02 Specification

## Summary
Cycle 02 is dedicated to the comprehensive implementation of the Integration Graph (Phase 3) and the fundamental logic for the 3-Way Diff mechanism. This cycle transitions the system from executing isolated parallel Coder cycles to merging their respective contributions into a cohesive whole. The core challenge involves implementing the `git_merge_node`, the `master_integrator_node`, and the `global_sandbox_node` within `src/graph.py`, along with the crucial `ConflictManager` in `src/services/conflict_manager.py`. By extracting the Base, Branch A, and Branch B states using Git commands, the Master Integrator can resolve conflicts semantically rather than relying on rudimentary text-based conflict markers. This phase guarantees that the combined outputs of the parallel cycles do not introduce systemic regressions.

## Infrastructure & Dependencies
- **A. Project Secrets (`.env.example`):** The Master Integrator LLM requires access to an advanced reasoning model. The Coder must ensure `OPENROUTER_API_KEY` or `JULES_API_KEY` is present in `.env.example` with the `# Target Project Secrets` comment.
- **B. System Configurations (`docker-compose.yml`):** The Integration Graph relies on local Git operations. The Coder must preserve the existing valid YAML and idempotency, ensuring no unintended volumes or permissions overwrite the necessary target project mounts.
- **C. Sandbox Resilience (CRITICAL TEST STRATEGY):** *All external API calls relying on the newly defined secrets in `.env.example` (specifically the LLM calls within the `master_integrator_node`) MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*. The sandbox evaluation will fail if tests attempt to resolve synthetic conflicts using live OpenRouter API calls.

## System Architecture
This cycle constructs the bridge between parallel execution and unified system testing.

**src/graph.py** (Modify)
- Implement `_create_integration_graph` connecting `git_merge_node` -> `master_integrator_node` -> `global_sandbox_node`.

**src/services/conflict_manager.py** (Modify/Create)
- Refactor or implement `build_conflict_package` to utilize `git show :1:{file}`, `:2:{file}`, and `:3:{file}` to construct the 3-Way Diff prompt.

**src/state.py** (Modify)
- Define or extend `IntegrationState` to hold the conflict payloads and resolution attempts.

**src/nodes/integration_nodes.py** (Create/Modify)
- Implement the actual node functions (`git_merge_node`, `master_integrator_node`, `global_sandbox_node`).

The architecture ensures that if a standard `git_merge_node` encounters a conflict, it routes strictly to the `master_integrator_node`, which then loops back to the merge attempt until successful, finally gating the process with the `global_sandbox_node`.

## Design Architecture
The design hinges on the robust definition of the `IntegrationState` and the structure of the conflict package. `IntegrationState` must be a strictly typed Pydantic model (`ConfigDict(extra='forbid', strict=True)`) containing lists of conflicted files, the current merge status, and the synthesized resolution code. The `ConflictManager` acts as the domain service, orchestrating the interaction between the file system (Git) and the state model. The 3-Way Diff prompt itself is a critical design element. It must clearly delineate the Base code from Branch A and Branch B to provide the LLM with unambiguous context. The consumers of this data are the `master_integrator_node` and ultimately the local Git repository when the resolution is applied. The system is designed for extensibility, allowing future iterations to inject different resolution strategies based on the file type (e.g., Python vs. JSON).

## Implementation Approach
1.  **State and Graph Construction:** Define the `IntegrationState` in `src/state.py`. Then, implement the `_create_integration_graph` in `src/graph.py`, establishing the nodes and conditional routing based on the merge status.
2.  **Conflict Manager Refactoring:** Within `src/services/conflict_manager.py`, implement the `build_conflict_package` method. Use the `subprocess` module to execute the specific `git show` commands, securely capturing the output for the Base, Local, and Remote file states. Construct the rigorous prompt template.
3.  **Integrator Node Logic:** Implement the `master_integrator_node` to invoke the LLM with the prepared conflict package and apply the returned resolution back to the file system.
4.  **Testing and Sandboxing:** Continuously validate the logic against the local sandbox. The Coder agent must mock the LLM response in all unit tests to ensure Sandbox Resilience.

## Test Strategy

### Unit Testing Approach (Min 300 words)
The unit testing strategy for the Integration Phase demands precise simulation of complex Git states. The Coder agent must utilize Pytest to extensively test the `ConflictManager` in isolation. The tests must employ `pytest-mock` to intercept the `subprocess.run` calls that execute the `git show` commands. By returning predefined string fixtures representing the Base, Local, and Remote code states, the unit tests can perfectly simulate a 3-Way Diff scenario without requiring a fragile, local Git repository setup. The assertions must verify that the `build_conflict_package` method correctly synthesizes these fixtures into the expected prompt structure. Furthermore, the `master_integrator_node` must be tested by mocking the LLM API response, injecting a synthetic "resolved" code block, and verifying that the node correctly updates the `IntegrationState` and attempts to write the resolution to the file system. This rigorous mocking guarantees Sandbox Resilience, ensuring the tests execute deterministically and swiftly without network dependencies or local repository corruption.

### Integration Testing Approach (Min 300 words)
Integration testing for the Phase 3 graph must validate the entire lifecycle of a merge conflict resolution. The tests must construct a localized, temporary Git repository (using a `tmp_path` fixture) to simulate the convergence of parallel cycles. The test setup will programmatically create a base file, branch off two divergent modifications, and attempt a merge to intentionally trigger a conflict. The integration test will then invoke the `_create_integration_graph`, mocking only the external LLM call within the `master_integrator_node` to return a known, successful resolution. The test must assert that the graph correctly routes from the failed `git_merge_node` to the `master_integrator_node`, applies the mocked resolution to the temporary repository, loops back to successfully complete the merge, and finally executes the `global_sandbox_node`. Crucially, adhering to the DB Rollback Rule, the temporary Git repository acts as the isolated persistent state, ensuring that the complex file system manipulations do not bleed into the main project directory or affect subsequent integration tests. This end-to-end validation within a controlled environment confirms the structural integrity of the integration pipeline.
