# CYCLE02: Integration Phase, 3-Way Diff, and UAT Separation

## Summary
Building upon the stable foundation established in CYCLE01, CYCLE02 implements the critical synchronisation and validation phases of the 5-Phase architecture. This cycle focuses on constructing Phase 3 (Integration Graph) and cleanly separating Phase 4 (UAT & QA Graph) into an independent lifecycle stage. The core technical challenge is implementing the robust 3-Way Diff conflict resolution mechanism. By replacing the rudimentary `<<<<<<<` marker analysis with a sophisticated comparison of the Base, Local (Branch A), and Remote (Branch B) code states, the Master Integrator agent can resolve complex merge conflicts intelligently. Finally, this cycle orchestrates the entire pipeline (`run_pipeline`), ensuring that Phase 4's end-to-end multi-modal UI testing only executes after a completely successful global integration in Phase 3.

## Infrastructure & Dependencies

This cycle relies on advanced Git operations and potentially UI testing frameworks (if Playwright is utilized in the mock).

### A. Project Secrets (`.env.example`)
The Coder must append the following required secret to the `.env.example` file. This is crucial for the UAT/QA phase if Vision models are used for diagnosing UI failures.
```bash
# Target Project Secrets
# (Required if the QA Auditor utilizes vision models for UI testing)
OPENROUTER_API_KEY=your_openrouter_api_key_here
```
*(Note: If `OPENROUTER_API_KEY` was already added in CYCLE01, simply ensure its presence is maintained.)*

### B. System Configurations (`docker-compose.yml`)
No specific new environment variables are strictly dictated by the prompt for this phase. The Coder must preserve valid YAML formatting and idempotency.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
**Mandate Mocking:** The Coder MUST explicitly mock all external API calls relying on the defined secrets (like `OPENROUTER_API_KEY`) and heavy file-system/Git operations in unit and integration tests (using `unittest.mock` or `pytest-mock`).

*Why:* The Sandbox will not possess the real API keys or a full Git environment during the autonomous evaluation phase. If tests attempt real network calls or complex Git merges against the host filesystem without valid setup, the pipeline will fail. This is a strict zero-trust requirement to prevent infinite CI loops.


## System Architecture

This section details the explicit code blueprints for implementing Phase 3 and isolating Phase 4. The objective is to construct a highly reliable integration mechanism capable of handling complex merge scenarios across multiple parallel development branches, entirely autonomously. This requires a significant departure from standard Git workflows, relying instead on a sophisticated 3-Way Diff analysis powered by large language models to understand and resolve conflicting code modifications conceptually. We must also ensure that the final User Acceptance Testing phase is strictly gated, executing only when the entire codebase is in a verified, pristine state.

**File Structure Overview:**
```text
/
├── src/
│   ├── **graph.py**               # Add _create_integration_graph & update UAT triggers
│   ├── services/
│   │   ├── **conflict_manager.py**# Implement 3-Way Diff payload generation
│   │   ├── **uat_usecase.py**     # Isolate as Phase 4 entrypoint
│   │   ├── **workflow.py**        # Orchestrate parallel Coder -> Integration -> UAT
│   │   └── ...
│   ├── domain_models/
│   │   └── **diff_package.py**    # Schema for 3-Way Diff (Base, Local, Remote)
│   └── ...
├── tests/
│   ├── nitpick/
│   │   ├── unit/
│   │   │   ├── **test_conflict_manager.py** # Unit test Git mock parsing
│   │   │   └── **test_workflow_orchestration.py** # Test phase transitions
│   │   └── integration/
│   │       └── **test_pipeline_orchestration.py** # E2E graph transitions (mocked LLMs)
```

### 1. 3-Way Diff Service (`src/services/conflict_manager.py`)
Refactor the conflict resolution logic to stop relying on raw conflict markers. Standard Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) are notoriously difficult for LLMs to parse and resolve reliably, often leading to mangled syntax and broken logic. Instead, we must implement the Pydantic schema and Git extraction logic to provide the LLM with the complete context: the original code, the changes made in branch A, and the changes made in branch B. This dramatically improves the model's ability to synthesize a correct resolution.

```python
# src/domain_models/diff_package.py (or similar schema file)
from pydantic import BaseModel, Field

class ConflictPackage(BaseModel):
    file_path: str = Field(..., description="Path to the conflicting file")
    base_code: str = Field(..., description="Code at the common ancestor")
    local_code: str = Field(..., description="Code in Branch A (Integration)")
    remote_code: str = Field(..., description="Code in Branch B (Incoming)")

# src/services/conflict_manager.py
# ... imports including ConflictPackage, subprocess, etc ...

class ConflictManager:
    # ... existing init ...

    def build_conflict_package(self, file_path: str) -> ConflictPackage:
        \"\"\"Extracts the 3 states of a conflicted file using Git.\"\"\"
        # MUST use proper async runner or subprocess.run in real implementation
        # Mocking this is critical for unit tests!
        try:
            base_cmd = f"git show :1:{file_path}"
            local_cmd = f"git show :2:{file_path}"
            remote_cmd = f"git show :3:{file_path}"

            base_code = self._execute_git_cmd(base_cmd)
            local_code = self._execute_git_cmd(local_cmd)
            remote_code = self._execute_git_cmd(remote_cmd)

            return ConflictPackage(
                file_path=file_path,
                base_code=base_code,
                local_code=local_code,
                remote_code=remote_code
            )
        except Exception as e:
            # Handle Git errors appropriately
            raise ValueError(f"Failed to build conflict package for {file_path}: {e}")
```

### 2. Integration Graph Creation (`src/graph.py`)
Define the new Phase 3 graph that runs after all parallel Phase 2 cycles complete. This graph represents a critical synchronization point. It transitions the system from highly parallel execution back into a sequential, single-threaded context where the global state of the application can be safely evaluated. It must be robust enough to handle severe merge conflicts without failing catastrophically, relying on the `Master Integrator` agent to untangle the logical knots created by concurrent development.

```python
# src/graph.py
from langgraph.graph import StateGraph, START, END
# ... import IntegrationState, nodes ...

def _create_integration_graph() -> StateGraph:
    workflow = StateGraph(IntegrationState) # Assuming a dedicated state

    workflow.add_node("git_merge_node", perform_git_merge)
    workflow.add_node("master_integrator_node", resolve_conflict_3way)
    workflow.add_node("global_sandbox_node", run_global_tests)

    workflow.add_edge(START, "git_merge_node")

    workflow.add_conditional_edges(
        "git_merge_node",
        route_merge, # Checks state for "conflict" or "success"
        {
            "conflict": "master_integrator_node",
            "success": "global_sandbox_node"
        }
    )

    workflow.add_edge("master_integrator_node", "git_merge_node") # Retry merge

    workflow.add_conditional_edges(
        "global_sandbox_node",
        route_global_sandbox, # Checks if global tests failed due to merge
        {
            "failed": "master_integrator_node", # Go back and fix the integration bug
            "pass": END
        }
    )

    return workflow.compile()
```

### 3. Workflow Orchestration (`src/services/workflow.py`)
Update the orchestrator to execute the phases in the correct sequence. The `WorkflowService` acts as the grand conductor of the entire pipeline. It must manage asynchronous task execution for Phase 2, gracefully handle timeouts and failures, and ensure that Phase 3 and Phase 4 only trigger when their prerequisites are perfectly satisfied.

```python
# src/services/workflow.py
import asyncio

class WorkflowService:
    # ...
    async def run_pipeline(self, cycles: list[CycleConfig]):
        \"\"\"Executes the full 5-Phase pipeline.\"\"\"

        # Phase 2: Parallel Coder Graph Execution
        tasks = [self.execute_cycle(cycle) for cycle in cycles]
        results = await asyncio.gather(*tasks)

        # Check if all cycles succeeded before proceeding
        if not all(r.success for r in results):
            raise PipelineError("Phase 2 failed. Not all parallel cycles completed.")

        # Phase 3: Integration Graph Execution
        integration_state = self.initialize_integration_state(results)
        integration_graph = _create_integration_graph()
        # ... execute graph and await completion ...

        if integration_result.status != "pass":
             raise PipelineError("Phase 3 Integration failed.")

        # Phase 4: UAT & QA Graph Execution
        # Isolated execution, only runs if Phase 3 is pristine
        qa_graph = _create_qa_graph()
        # ... execute qa graph ...
```
## Design Architecture

This cycle emphasises clean architectural boundaries. The `ConflictPackage` Pydantic schema is the cornerstone of the 3-Way Diff implementation, ensuring the LLM (Master Integrator) receives highly structured, context-rich data rather than raw, potentially corrupted text files.

**Domain Concept: `ConflictPackage`**
The `ConflictPackage` model strictly defines the contract between the Git filesystem and the LLM integration agent.

*   **Key Invariants & Constraints:**
    *   `file_path`, `base_code`, `local_code`, and `remote_code` must be present. If Git cannot retrieve the base ancestor (e.g., due to an octopus merge or shallow clone issues), the system must handle this gracefully, potentially falling back to a 2-way diff or alerting the user, rather than passing `None` to a strictly typed string field.
*   **Consumers and Producers:**
    *   *Producers:* `ConflictManager.build_conflict_package` executes Git shell commands and populates this model.
    *   *Consumers:* The `master_integrator_node` receives this model. The LLM prompt is constructed deterministically using these exact fields, providing a clear "Before/Branch A/Branch B" view.

**Separation of Concerns (Phase 4):**
The `uat_usecase.py` service must be completely decoupled from the Phase 2 implementation loops. Previously, Coder agents might have attempted to trigger UAT tests prematurely. Phase 4 is now strictly an *inter-cycle* orchestration concern, managed solely by the `WorkflowService` after the `_create_integration_graph` reaches its `END` node successfully.


## Implementation Approach

The implementation of Phase 3 and Phase 4 represents the most complex orchestration challenge in the system. We must proceed methodically, building from the lowest-level Git operations up to the high-level asynchronous orchestration logic. This ensures that the foundation is solid before we attempt to coordinate multiple LangGraph executions concurrently.

1.  **3-Way Diff Logic:** Begin in `src/services/conflict_manager.py`. Implement the `ConflictPackage` schema (or place it in the appropriate `domain_models` directory). Develop the `build_conflict_package` method, carefully handling the asynchronous execution of `git show :1:`, `:2:`, `:3:` commands. Update the prompt template used by the `master_integrator_node` to consume this new data structure instead of raw conflict markers. This is the most crucial step; if the LLM receives malformed diffs, the entire integration phase will fail. We must meticulously test the edge cases where Git history is sparse or anomalous.
2.  **Integration Graph:** Construct `_create_integration_graph` in `src/graph.py`. Define the new state model (`IntegrationState`) if necessary. Implement the `git_merge_node` (which attempts the merge and flags conflicts), the `master_integrator_node` (which utilises the 3-Way Diff service), and the `global_sandbox_node` (which runs the full test suite). Wire these together with conditional routing. Ensure that the graph logic robustly handles the loop between the merge node and the integrator node, preventing infinite retry loops if a conflict is mathematically unresolvable.
3.  **UAT Isolation:** Refactor `src/services/uat_usecase.py`. Ensure it no longer accepts individual `CycleState` objects as its primary trigger, but rather an overarching pipeline configuration. Remove any lingering dependencies or triggers originating from Phase 2 nodes. This isolation is critical for system stability. UAT must only ever execute against a codebase that has successfully navigated the `global_sandbox_node` in Phase 3. Any violation of this rule compromises the integrity of the test results.
4.  **Pipeline Orchestrator:** Finally, update `src/services/workflow.py` to bind the entire sequence together. Implement the `asyncio.gather` logic for Phase 2, followed by the sequential execution of Phase 3, and conditionally triggering Phase 4 upon success. The orchestrator must handle exceptions elegantly at every layer, providing informative error messages and ensuring that partial failures do not leave the repository in a corrupted state. We must utilize comprehensive try/except blocks and rigorous state validation before transitioning between major phases.


## Test Strategy

Testing for CYCLE02 focuses heavily on mocking complex Git interactions and validating the sequential orchestration of the massive LangGraph pipeline. We must prove that the system can handle concurrent execution, complex merge conflicts, and multi-modal UAT failures without crashing or deadlocking. The tests must be highly resilient and completely decoupled from actual network calls or live Git repositories.

**Unit Testing Approach (Min 300 words):**
The most critical unit test involves the `ConflictManager`. In `tests/nitpick/unit/test_conflict_manager.py`, we must mock the `_execute_git_cmd` (or `subprocess.run`) method. We will simulate scenarios where Git returns valid code strings for all three states (Base, Local, Remote), and test edge cases where an ancestor might be missing (simulating a Git error). We must assert that the `ConflictPackage` schema is hydrated correctly with the mocked strings and that validation errors are raised if required fields are missing. Additionally, we will unit test the new routing functions in `src/graph.py` (e.g., `route_merge`) to ensure they handle the `IntegrationState` correctly (routing to conflict resolution or global sandbox based on flags). We must thoroughly test the asynchronous orchestration logic in `WorkflowService`. Create a suite of tests that mock the return values of the individual phase execution functions. We must prove that if Phase 2 fails, Phase 3 is never invoked. We must prove that if Phase 3 fails, Phase 4 is never invoked. This rigorous testing of the control flow is essential for guaranteeing the overall stability of the 5-Phase architecture.

**Integration Testing Approach (Min 300 words):**
Integration testing will focus on the `WorkflowService` orchestration in `tests/nitpick/integration/test_pipeline_orchestration.py`. We will mock out the actual `_create_coder_graph`, `_create_integration_graph`, and `_create_qa_graph` functions, replacing them with simple async functions that return predefined success or failure states. We will then execute `run_pipeline` with a mock set of multiple cycles. We must assert that:
1.  The `asyncio.gather` mechanism correctly awaits all mock Phase 2 tasks concurrently.
2.  If one Phase 2 task returns failure, Phase 3 is *not* executed, and the pipeline halts appropriately.
3.  If all Phase 2 tasks succeed, the mock Phase 3 graph is executed exactly once.
4.  Phase 4 (UAT) is only executed if Phase 3 returns a pristine success state.
This ensures the high-level control flow is robust before we attempt full End-to-End testing with the Marimo tutorials. Ensure all test database interactions (if any exist for state tracking) utilize strict transaction rollback fixtures. Furthermore, we must create a dedicated integration test for the 3-Way diff logic. Using `pyfakefs`, construct a temporary, isolated Git repository. Programmatically create a commit history that guarantees a complex merge conflict across multiple files. Execute the Integration Graph against this mock repository, substituting the real LLM calls with deterministic mock responses. Assert that the Integration Graph correctly identifies the conflict, generates the correct payload, routes to the mocked integrator, and successfully applies the resulting patch, completing the merge. This is the ultimate proof that the autonomous integration engine functions correctly.
