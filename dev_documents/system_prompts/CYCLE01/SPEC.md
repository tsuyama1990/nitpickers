# CYCLE01 Specification

## Summary
CYCLE01 focuses on refactoring the core state management, routing logic, and integration conflict handling mechanisms necessary to support the new 5-Phase architecture. This cycle explicitly avoids modifying the high-level graph orchestration, deferring that complex wiring to CYCLE02. The primary objective is to enhance `CycleState` with new flags (`is_refactoring`, `current_auditor_index`), enabling a robust, sequential auditor pipeline and distinct implementation vs. refactoring phases. Additionally, we will rewrite the conflict resolution logic in `src/services/conflict_manager.py` to construct a true 3-way diff (Base, Branch A, Branch B) instead of relying on naive Git conflict marker parsing, empowering the master integrator agent with superior context.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
-   **No new secrets are required for this specific cycle.**
-   The existing `JULES_API_KEY`, `E2B_API_KEY`, and `OPENROUTER_API_KEY` remain sufficient for the current orchestration.
-   Explicit instruction to Coder: Do not append any new services to `.env.example` in this cycle.

### B. System Configurations (`docker-compose.yml`)
-   **No new system configurations are required for this cycle.**
-   Explicit instruction to Coder: Do not modify `docker-compose.yml` in this cycle. Preserve valid YAML formatting and idempotency.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
-   **Mandate Mocking:** You MUST explicitly instruct the Coder that *all external API calls relying on the defined secrets in `.env.example` MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*.
-   *Why:* The Sandbox will not possess the real API keys during the autonomous evaluation phase. If tests attempt real network calls to SaaS providers without valid `.env` values, the pipeline will fail and cause an infinite retry loop. Any tests dealing with the new routing logic or state validation must operate entirely on mocked inputs without instantiating real network clients.

## System Architecture

The following files represent the core components modified during this cycle:

```text
src/
├── **state.py**                (Adding new fields to CycleState and CommitteeState)
├── nodes/
│   └── **routers.py**          (Implementing route_sandbox_evaluate, route_auditor, route_final_critic)
└── services/
    └── **conflict_manager.py** (Rewriting build_conflict_package for 3-way diffs)
```

## Design Architecture

This system relies on robust Pydantic-based schemas to define the domain concepts and enforce invariants.

### `src/state.py`
The domain model `CycleState` acts as the single source of truth for the LangGraph pipeline. In this cycle, we extend the `CommitteeState` sub-model (which is composed into `CycleState`) with the following fields:

-   `is_refactoring: bool`: (Default: `False`). This boolean flag fundamentally changes the graph's routing behavior. When `False`, a successful sandbox evaluation routes the code to the serial Auditor pipeline. When `True`, it signifies that the code has already passed the audits and is undergoing final polish, routing it to the `final_critic_node`.
-   `current_auditor_index: int`: (Default: `1`). This integer tracks the progression of the serial audit loop (typically 1 to 3). It must be constrained using Pydantic's `Field(ge=1)` and validated to prevent runaway loops.
-   `audit_attempt_count: int`: (Default: `0`). This integer limits the number of times a single auditor can reject the code and force a rewrite. It prevents infinite loops caused by an agent's inability to satisfy an overly strict auditor prompt.

These additions maintain backward compatibility via property delegates defined directly on `CycleState` (e.g., `@property def is_refactoring(self) -> bool: return self.committee.is_refactoring`).

### `src/services/conflict_manager.py`
The `ConflictManager` currently extracts conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`). The new design architecture dictates a cleaner, context-rich approach. Instead of parsing messy merged files, the system will use raw Git commands (`git show :1:file`, `:2:file`, `:3:file`) to extract the exact state of the Base commit, the Local branch, and the Remote branch. This raw data will be formatted into a structured prompt package (the "3-Way Diff"), providing the LLM with the unambiguous, pristine code blocks it needs to safely reconstruct the file.

## Implementation Approach

1.  **Update `src/state.py`**:
    -   Locate `CommitteeState`. Add `is_refactoring` (bool, default False) and ensure `current_auditor_index` and `audit_attempt_count` are present and properly typed with Pydantic constraints (`Field(ge=0)`).
    -   Locate `CycleState`. Add property getters and setters for the newly added `CommitteeState` fields to maintain API compatibility for existing nodes that access them directly off the root state.
2.  **Implement Routing Logic in `src/nodes/routers.py`**:
    -   Implement `route_sandbox_evaluate(state: CycleState) -> str`: If `state.get("sandbox_status")` (or equivalent test status) is failed, return "failed". If passed, and `state.is_refactoring` is True, return "final_critic". Otherwise, return "auditor".
    -   Implement `route_auditor(state: CycleState) -> str`: Check the current auditor's feedback. If rejected, increment `audit_attempt_count` and return "reject" (handling max attempts gracefully). If approved, increment `current_auditor_index`. If the index exceeds the maximum auditor count (e.g., 3), return "pass_all". Otherwise, return "next_auditor".
    -   Implement `route_final_critic(state: CycleState) -> str`: Evaluate the final critic's decision. Return "approve" or "reject".
3.  **Refactor `build_conflict_package` in `src/services/conflict_manager.py`**:
    -   Modify the method signature to accept a specific file path and the Git commit hashes/branch names representing the Base, Local, and Remote states.
    -   Utilize the project's asynchronous `ProcessRunner` (or `GitManager`) to execute `git show :1:{filepath}`, `git show :2:{filepath}`, and `git show :3:{filepath}`.
    -   Construct a formatted string payload containing the `### Base`, `### Branch A`, and `### Branch B` sections, injecting the stdout from the Git commands. Ensure strict handling of stderr if a file didn't exist in one of the states (e.g., a newly created file conflicting with a deletion).

## Test Strategy

### Unit Testing Approach
Unit tests must meticulously verify the Pydantic constraints and the pure functions within the routers. For `state.py`, construct `CycleState` objects with invalid `current_auditor_index` values (e.g., 0 or -1) and assert that `pydantic.ValidationError` is raised. Verify that setting properties on the root `CycleState` correctly mutates the underlying `CommitteeState`. For `routers.py`, create dozens of permutations of `CycleState` (failed tests, passing tests, varying `is_refactoring` flags) and use `pytest.mark.parametrize` to assert that `route_sandbox_evaluate`, `route_auditor`, and `route_final_critic` return the exact expected string literal in every scenario. These tests must run completely offline without instantiating any graph components.

### Integration Testing Approach
Integration testing will focus on the complex Git interactions within `conflict_manager.py`. We must create a robust Pytest fixture that initializes a temporary, bare Git repository. This fixture will programmatically create a base commit with a shared file, create two diverging branches, modify the file incompatibly on both branches, and then attempt a merge to intentionally induce a conflict state. Once the repository is in this state, the test will invoke `build_conflict_package`. The assertion must verify that the resulting string payload contains the exact contents of the original base file, the modifications from Branch A, and the modifications from Branch B, perfectly isolated under their respective `###` markdown headers. We will also test the edge case where a file is modified on one branch but deleted on the other, ensuring the Git commands handle the `:1:`, `:2:`, and `:3:` resolution correctly without crashing the application. All DB/State rollbacks must be handled by Pytest fixtures.