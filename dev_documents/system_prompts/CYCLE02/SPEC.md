# CYCLE02 Specification: Integration and QA Automation

## Summary
This document outlines the precise specifications for `CYCLE02` of the NITPICKERS 5-Phase architecture redesign. This cycle focuses on integrating the disparate features generated in `CYCLE01` and formalizing the final automated QA processes. We will develop the sophisticated 3-Way Diff resolution service within `src/services/conflict_manager.py` to seamlessly handle Git merge conflicts using AI. We will then construct the entirely new `_create_integration_graph` in `src/graph.py` to automate this resolution and validate the merged codebase in a global sandbox. Finally, we will decouple the User Acceptance Testing (UAT) logic from the coder phase, establishing a dedicated Phase 4 (`_create_qa_graph`) driven by multi-modal Vision LLMs to diagnose and remediate UI regressions autonomously.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
During `CYCLE02`, the infrastructural dependencies expand to include the Vision LLMs required for the QA Auditor node. The Coder must ensure the following variables are appended to the target project's `.env.example` file.

```dotenv
# Target Project Secrets
OPENROUTER_API_KEY="your_openrouter_api_key_here"  # Required for Vision models (e.g., anthropic/claude-3-opus)
JULES_API_KEY="your_jules_api_key_here"
E2B_API_KEY="your_e2b_api_key_here"
```

### B. System Configurations (`docker-compose.yml`)
The Integration Phase and QA Phase run sequentially after all Coder phases. No new exposed ports are strictly required, but the Coder must ensure the `environment:` section for the main agent service in `docker-compose.yml` passes through the necessary keys. Preserve all existing valid YAML formatting and idempotency.

### C. Sandbox Resilience
**CRITICAL TEST STRATEGY MANDATE:** The Coder MUST explicitly mock all external API calls relying on the newly defined secrets in unit and integration tests (using `unittest.mock` or `pytest-mock`).
*Why:* The Sandbox will not possess the real API keys during autonomous test execution. If tests attempt real network calls to OpenRouter for screenshot analysis without valid `.env` values, the pipeline will fail and cause an infinite retry loop. Specifically, the `master_integrator_node` and `qa_auditor` calls must be rigorously stubbed.

## System Architecture
This cycle constructs Phase 3 (Integration) and formalizes Phase 4 (QA).

**File Structure Overview:**
```text
src/
├── **graph.py**                 # Modification: Add _create_integration_graph, refine _create_qa_graph
├── services/
│   ├── **conflict_manager.py**  # Modification: Implement 3-Way Diff parsing logic
│   ├── **uat_usecase.py**       # Modification: Decouple from Coder Phase
│   └── **workflow.py**          # Modification: Orchestrate Phase 2 -> Phase 3 -> Phase 4
├── nodes/
│   ├── **integration.py**       # Modification: Implement git_merge, master_integrator, global_sandbox nodes
```

### Structural Blueprints

**1. Conflict Manager Service (`src/services/conflict_manager.py`)**
This service acts as the bridge between Git and the LLM, extracting the exact state of a file during a conflict.

```python
import asyncio
# ... assumes a ProcessRunner utility exists in the project ...

class ConflictManager:
    # ... existing scan_conflicts method ...

    async def build_conflict_package(self, file_path: str) -> str:
        """
        Extracts the Base, Local, and Remote versions of a conflicted file
        and constructs the 3-Way Diff prompt for the Master Integrator.
        """
        # Pseudo-code utilizing a presumed async ProcessRunner
        # Base code: git show :1:{file_path}
        # Local code: git show :2:{file_path}
        # Remote code: git show :3:{file_path}

        # 1. Execute git commands asynchronously
        # 2. Handle potential errors if a specific stage doesn't exist (e.g., added in both branches)
        # 3. Construct the prompt string:

        prompt_template = f"""
        あなた（Master Integrator）の任務は、Gitのコンフリクトを安全に解消することです。
        以下の共通祖先（Base）のコードに対して、Branch AとBranch Bの変更意図を両立させた、最終的な完全なコードを生成してください。

        ### Base (元のコード)
        ```python
        {{base_code}}
        ```

        ### Branch A の変更 (Local)
        ```python
        {{local_code}}
        ```

        ### Branch B の変更 (Remote)
        ```python
        {{remote_code}}
        ```
        """
        # Return the formatted string
        pass
```

**2. Integration Graph Orchestration (`src/graph.py`)**
A new graph must be defined to handle the sequential integration of completed cycles.

```python
from langgraph.graph import StateGraph, START, END
# ... import integration nodes ...

# Assume an IntegrationState Pydantic model exists
def _create_integration_graph() -> StateGraph:
    workflow = StateGraph(IntegrationState)

    # Add Nodes
    workflow.add_node("git_merge_node", git_merge_execution)
    workflow.add_node("master_integrator_node", master_integrator_resolution)
    workflow.add_node("global_sandbox_node", global_sandbox_evaluation)

    # Define Edges
    workflow.add_edge(START, "git_merge_node")

    # Conditional edge from merge attempt
    workflow.add_conditional_edges(
        "git_merge_node",
        route_merge, # Function to check if merge was successful or conflicted
        {
            "conflict": "master_integrator_node",
            "success": "global_sandbox_node"
        }
    )

    # Re-attempt merge after resolution
    workflow.add_edge("master_integrator_node", "git_merge_node")

    # Conditional edge after global sandbox evaluation
    workflow.add_conditional_edges(
        "global_sandbox_node",
        route_global_sandbox, # Function to check if tests passed
        {
            "failed": "master_integrator_node", # Route back for fixing integration regressions
            "pass": END
        }
    )

    return workflow.compile()
```

**3. Workflow Orchestration (`src/services/workflow.py`)**
The main entry point must be updated to run the phases sequentially.

```python
# Pseudo-code for main execution flow
async def run_pipeline():
    # Phase 2: Parallel Coder Graph Execution
    # ... logic to run _create_coder_graph for Cycle 1...N concurrently ...
    # await asyncio.gather(*tasks)

    # Phase 3: Integration
    # if all coder cycles completed successfully:
    #    integration_graph = _create_integration_graph()
    #    await integration_graph.ainvoke(initial_state)

    # Phase 4: UAT & QA
    # if integration completed successfully:
    #    qa_graph = _create_qa_graph()
    #    await qa_graph.ainvoke(initial_state)
    pass
```

## Design Architecture
This section details the pre-implementation design for the robust mechanisms introduced in `CYCLE02`.

The primary design challenge in this cycle is bridging the gap between external system state (Git) and internal AI reasoning (LangGraph). The `ConflictManager` service acts as an Anti-Corruption Layer. Instead of polluting the LangGraph nodes with raw subprocess calls and Git syntax parsing, this service encapsulates that complexity. It guarantees that the `master_integrator_node` always receives a clean, strongly typed `ConflictPackage` (or a well-formatted string prompt acting as one) containing exactly the three discrete file versions required for safe resolution.

**Key Invariants and Constraints:**
1.  **Strict 3-Way Isolation**: The system must never feed standard Git conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) directly to the LLM. Experience dictates that LLMs often struggle to parse these markers reliably, leading to corrupted code generation. The strict isolation of Base, Local, and Remote blocks is non-negotiable.
2.  **Sequential Phase Enforcement**: Phase 3 (`Integration Graph`) cannot begin until Phase 2 (`Coder Graph` parallel cycles) has completely finished and generated pull requests. Phase 4 (`QA Graph`) cannot begin until Phase 3 has successfully executed a global `pytest` and `ruff check` suite.
3.  **Stateless QA Auditing**: The `qa_auditor` in Phase 4 must operate entirely statelessly. It receives only the multi-modal artifacts (Playwright screenshots, DOM dumps, error logs) and outputs a structured JSON fix plan. It must not retain context from the Coder phase; it acts purely as a fresh set of eyes.

**Consumers and Producers:**
-   **Producers:** The `git_merge_node` produces the conflict state. The `uat_evaluate` node (in Phase 4) produces the multi-modal error artifacts.
-   **Consumers:** The `master_integrator_node` consumes the `ConflictManager`'s output to generate merged code. The `qa_auditor` consumes the multi-modal artifacts to generate remediation plans. The `WorkflowService` consumes the final `END` state of each phase to trigger the next.

## Implementation Approach
The implementation of `CYCLE02` requires careful orchestration of asynchronous processes and LLM interactions.

**Step 1: 3-Way Diff Implementation**
Begin in `src/services/conflict_manager.py`. Implement the `build_conflict_package` method. You must use the project's established asynchronous `ProcessRunner` (or `asyncio.create_subprocess_exec`) to execute the `git show :1:...`, `:2:...`, and `:3:...` commands. Ensure robust error handling; if a file was newly created in one branch, the base or remote version might not exist (git returns an error code). The method must gracefully handle these edge cases and construct the final prompt template as specified in the blueprint.

**Step 2: Construct the Integration Graph**
Open `src/graph.py` and define `_create_integration_graph`. Implement the required nodes in `src/nodes/integration.py`. The `git_merge_node` should attempt a standard `git merge --no-commit`. If it fails due to conflicts, update the `IntegrationState` to reflect the conflicted files. The `master_integrator_node` will iterate through these files, utilizing the `ConflictManager` to generate prompts, calling the JULES LLM, and writing the unified code back to disk. The `global_sandbox_node` executes the project's standard `uv run pytest` and `uv run ruff check` commands. Wire the graph using the specified conditional logic.

**Step 3: Decouple UAT and Orchestrate Phases**
Modify `src/services/uat_usecase.py` to ensure it no longer assumes it is part of the Coder phase. It should be triggered independently. Finally, update `src/services/workflow.py`. Implement the `run_pipeline` orchestration logic. Use `asyncio.gather` to execute the coder graphs in parallel. Await their completion, verify success, and then sequentially invoke the integration graph, followed by the QA graph.

## Test Strategy

### Unit Testing Approach (Min 300 words)
The unit tests for `CYCLE02` must aggressively mock file system and subprocess interactions to ensure stability and speed.

1.  **Conflict Manager Validation:** Create a comprehensive test suite for `src/services/conflict_manager.py`.
    -   *Assertion (Happy Path):* Use `unittest.mock.patch` to intercept the `ProcessRunner` calls within `build_conflict_package`. Configure the mock to return specific string payloads representing "Base Code", "Local Code", and "Remote Code" when the respective `git show` commands are executed. Assert that the resulting prompt string accurately incorporates these payloads within the predefined Markdown headers.
    -   *Assertion (Edge Case - New File):* Configure the mock `ProcessRunner` to simulate an error (non-zero exit code) when attempting to fetch the Base code (`git show :1...`), simulating a file added in both branches. Assert that the `build_conflict_package` method handles this gracefully, perhaps by injecting an empty string or a specific placeholder for the Base section, rather than crashing the pipeline.

2.  **Integration Node Logic Verification:** Test the core logic of the nodes without invoking the LangGraph framework.
    -   *Assertion (`master_integrator_node`):* Mock the `ConflictManager` and the LLM execution call. Pass a mock `IntegrationState` indicating a conflict. Assert that the node correctly calls the `ConflictManager` for the conflicted file, calls the LLM with the generated prompt, and attempts to write the mock LLM response back to the file system (mocked).

**Sandbox Resilience Rule:** Under no circumstances should these tests attempt real `git merge` operations on the actual repository hosting the tests, as this will irreparably corrupt the CI environment.

### Integration Testing Approach (Min 300 words)
Integration testing for `CYCLE02` focuses on the orchestration flow and the resilience of the QA automation loop.

1.  **Workflow Phase Transitions:**
    -   *Assertion:* Construct a test for the main `run_pipeline` function in `src/services/workflow.py`. Mock the `ainvoke` methods of the three graph objects (`_create_coder_graph`, `_create_integration_graph`, `_create_qa_graph`). Configure the mocks to return success states immediately. Execute the pipeline. Assert, using `mock.assert_called_once()`, that the graphs were executed in the correct sequential order (Coder -> Integration -> QA), verifying the fundamental phase boundaries.

2.  **QA Graph Remediation Loop:**
    -   *Assertion:* We must verify the automated recovery capabilities of Phase 4 without real browser execution. Compile the `_create_qa_graph`. Mock the `uat_evaluate` node to return a simulated Playwright failure state (e.g., providing a dummy error trace string and a mock image path). Mock the `qa_auditor` (Vision LLM) to return a structured JSON string indicating a simple fix (e.g., "Change button color to red"). Mock the `qa_session` to simulate applying the fix. Execute the graph.
    -   Assert that the execution trace follows: `uat_evaluate` (Fail) -> `qa_auditor` -> `qa_session` -> `uat_evaluate` (Mocked Success) -> `END`. This proves the cyclical self-healing capability of the final QA gate.

**DB Rollback Rule Compliance:** Any integration tests that modify dummy configuration files or track workflow state in a persistent manner must utilize standard `pytest` fixtures to encapsulate the execution within a database transaction, explicitly rolling it back to guarantee a pristine environment for all subsequent assertions.