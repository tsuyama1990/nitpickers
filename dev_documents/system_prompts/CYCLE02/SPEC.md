# CYCLE02 SPEC: Integration & UAT Automation (Phases 3 & 4)

## Summary

CYCLE02 represents the culmination and finalization of the Nitpickers 5-Phase Architecture by implementing the critical integration and final validation stages. This cycle is where the parallel, isolated development efforts of Phase 2 are brought together, merged into a cohesive whole, and rigorously tested from an end-to-end perspective. The successful execution of Phase 3 (Integration Phase) and Phase 4 (UAT & QA Graph) is what truly distinguishes Nitpickers as a robust, enterprise-grade AI development environment, capable of handling complex, multi-agent workflows without descending into chaotic merge conflicts or releasing broken code. This cycle ensures the system can autonomously resolve Git conflicts and validate the holistic application state in a safe, automated manner.

Phase 3 (Integration Phase) introduces a sophisticated, robust 3-Way Diff mechanism to handle Git merge conflicts gracefully. This is a massive leap forward from simple "PR Merges" that often fail when multiple agents modify the same files concurrently. Instead of relying on naive textual merges or simply throwing a file full of raw `<<<<<<< HEAD` conflict markers at an LLM and hoping for the best, the Integration Phase employs an AI-assisted `master_integrator_node`. This specialized agent is provided with deeply contextualized information: it understands the common ancestor (the Base code), the changes made in the current integration branch (the Local code), and the incoming changes from the feature branch (the Remote code). By analyzing these three distinct perspectives, the Integrator can intelligently synthesize a resolution that honors the intent of both branches, ensuring a smooth, mathematically sound merge process.

Phase 4 (UAT & QA Graph) formally separates the User Acceptance Testing from the individual coder cycles. This is a critical architectural boundary. In the previous iteration, agents might have attempted to run E2E tests prematurely on their isolated feature branches, leading to false negatives or tests failing due to missing dependencies from other parallel workstreams. Now, the QA Graph runs strictly *only* once all feature branches are successfully integrated into the main `int` branch and the `global_sandbox_node` has verified structural integrity. This ensures that the E2E tests are validating the true, final state of the software. If a bug is discovered during this final phase, a dedicated `qa_auditor` and `qa_session` are spun up to diagnose and automatically remediate the issue, guaranteeing that the final output is not just compiled, but functionally verified against user requirements.

The overarching goal of CYCLE02 is to build a resilient, automated pipeline that handles the messy realities of software integration. It achieves this by moving away from fragile, single-threaded execution and embracing a sophisticated, multi-stage reconciliation process. The 3-Way Diff logic is the cornerstone of this resilience, providing the AI with the exact context it needs to resolve conflicts that would otherwise require human intervention. Simultaneously, the isolated QA Graph acts as the final safety net, ensuring that no code is marked complete until it has passed rigorous, automated E2E testing in a fully integrated environment. This cycle is what transforms Nitpickers from a code generation tool into a true, autonomous software factory.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
*   **External Services**: No new external APIs are required for the core integration or UAT routing logic. The system continues to rely fundamentally on `JULES_API_KEY`, `OPENROUTER_API_KEY`, and `E2B_API_KEY` for its AI operations.
*   **Action**: Ensure `.env.example` remains fully documented with these keys under the `# Target Project Secrets` heading, clearly indicating to new users what is required for full pipeline execution.

### B. System Configurations (`docker-compose.yml`)
*   **Environment Setups**: The integration logic, particularly the Git commands executed by the `ConflictManager`, relies heavily on the local environment executing the container. It is imperative that the `TARGET_PROJECT_PATH` is mounted correctly so the container can perform real Git operations on the host repository.
*   **Action**: Preserve the existing YAML formatting. Ensure that the volume mounts for the target project are correctly configured and that no new agent configurations override the established deployment pattern.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
*   **Mandate Mocking**: You MUST explicitly mock all Git commands executed by the `ConflictManager` during unit and integration tests. This includes commands like `git merge`, `git show :1:{file}`, `git show :2:{file}`, and `git show :3:{file}`.
*   **Why**: Unit tests must not mutate the actual host repository or rely on complex, non-deterministic Git states (like an actual merge conflict existing on the developer's machine). We must test the *logic* of the 3-Way diff construction and the routing of the Integration Graph, not the underlying Git binary itself. Mocking these commands guarantees fast, deterministic, and safe test execution across all environments.

## System Architecture

The implementation targets the brand new Phase 3 and Phase 4 LangGraphs, along with a significant overhaul of the `ConflictManager` service. This architecture is designed to orchestrate the complex transition from parallel development back into a single, unified, and fully tested codebase. The new nodes and state models introduced here are explicitly tailored to handle integration failures and global validations, ensuring a robust end-to-end pipeline.

The file structure required to implement Phase 3 and Phase 4 touches the core graph definitions, the state management, the integration-specific nodes, and the overarching workflow orchestrator. The additions are substantial, completely formalizing the final stages of the Nitpickers development lifecycle.

```ascii
src/
├── **graph.py**                  # Create _create_integration_graph and adjust _create_qa_graph logic
├── nodes/
│   ├── routers.py            # (If necessary, add route_merge, route_global_sandbox to handle integration branching)
│   └── **integration_nodes.py**  # Implement new nodes: git_merge_node, master_integrator_node, global_sandbox_node
├── services/
│   ├── **conflict_manager.py**   # Major rewrite: build_conflict_package now constructs the 3-Way Diff prompt
│   ├── **uat_usecase.py**        # Adjust to receive QaState only after the Integration Phase is complete
│   └── **workflow.py**           # Orchestrate parallel Coder phases -> sequential Integration -> sequential QA
└── **state.py**                  # Create brand new IntegrationState and QaState Pydantic models
```

The most significant architectural addition in this cycle is the creation of `_create_integration_graph` within `src/graph.py`. This new LangGraph is responsible for taking a completed feature branch from Phase 2 and attempting to merge it into the main integration (`int`) branch. The topology is highly specialized for conflict resolution. It begins at the `START` node and proceeds immediately to the `git_merge_node`. If the merge is a clean fast-forward or auto-resolves, a conditional edge routes execution to the `global_sandbox_node` for structural verification. However, if a Git conflict is detected, the routing logic diverts the flow to the `master_integrator_node`. This AI agent, armed with the 3-Way Diff package, attempts to resolve the conflict. Once resolved, the graph loops back to the `git_merge_node` to retry the merge, creating a robust, self-healing integration loop.

Simultaneously, the `ConflictManager` service located in `src/services/conflict_manager.py` undergoes a massive conceptual shift. Previously, resolving conflicts might have involved naive string replacement or sending the entire file with `<<<<<<< HEAD` markers to an LLM. The new architecture dictates a precise 3-Way Diff approach. The `ConflictManager` must leverage the project's asynchronous `ProcessRunner` to execute specific Git commands against the repository index. By running `git show :1:{file}`, it extracts the common ancestor (Base). Running `git show :2:{file}` extracts the target branch state (Local). Finally, `git show :3:{file}` extracts the incoming branch state (Remote). The `build_conflict_package` method then takes these three distinct strings and formats them into a highly structured Markdown prompt, giving the `master_integrator_node` the exact context required to perform a semantic, intelligent merge.

The final piece of the architectural puzzle is the isolation of Phase 4. The `_create_qa_graph` must be adjusted to ensure it is completely decoupled from the individual coder cycles. It is triggered only by `src/services/workflow.py` after the entire Phase 3 Integration loop has successfully completed for all branches. The QA Graph operates on its own dedicated `QaState`, executing the `uat_evaluate` node (running Playwright E2E tests, for example). If a failure occurs, it routes to a specialized `qa_auditor` to analyze logs and screenshots, and then to a `qa_session` to apply fixes to the integrated codebase, looping until the tests pass. This strict separation guarantees that the system is always testing the final, unified product, preventing false positives and ensuring true release readiness.

## Design Architecture

This cycle focuses intensely on handling multi-branch integration and providing a framework for end-to-end validation. The design architecture relies on strictly typed Pydantic models to manage the complex data associated with Git conflicts, merge states, and test execution logs, ensuring that the integration and QA agents have precise, predictable context.

The domain concepts represented in each file are critical to understanding how the system maintains control over the final stages of the software lifecycle. By formalizing these concepts into robust state models and specialized nodes, we guarantee the stability of the integration process and the reliability of the final test outcomes.

### 1. `src/state.py`
*   **Domain Concept**: The new state models, `IntegrationState` and `QaState`, represent the context for Phase 3 and Phase 4, respectively. They must hold strictly typed primitives to guarantee routing determinism during the critical integration and testing loops.
*   **Modifications**:
    *   **IntegrationState**: This model represents the state of the integration branch (`int`). It must track the `merge_status` (e.g., success, conflict, failed), a list of `conflicting_files`, and crucially, the structured `3-Way Diff` packages generated by the `ConflictManager` to be passed to the LLM. It must also track which specific cycle branch is currently being merged.
    *   **QaState**: This model represents the state of the final E2E test run (Phase 4). It holds the `test_status` (pass/fail), raw `test_logs`, paths to captured `screenshots` (for the vision-capable `qa_auditor`), and the current iteration count of the QA remediation loop.
*   **Key Invariants**: The state models must enforce strict invariants to guarantee routing stability. For `IntegrationState`, if `merge_status` is "conflict", the `conflicting_files` list must not be empty. For `QaState`, the remediation loop must have a defined maximum limit to prevent infinite debugging cycles.
*   **Expected Consumers**: The primary consumers are the new integration nodes (`git_merge_node`, `master_integrator_node`, `global_sandbox_node`) and the QA nodes (`uat_evaluate`, `qa_auditor`, `qa_session`), which read and mutate these specific state objects during their execution phases.

### 2. `src/graph.py`
*   **Domain Concept**: The orchestration of `_create_integration_graph` and `_create_qa_graph`. These functions define the exact sequence of execution for merging code and verifying the final application state.
*   **Modifications**:
    *   `_create_integration_graph`: Orchestrates the attempt to merge a feature branch (`git_merge_node`). The topology must include conditional edges: if successful, it routes to `global_sandbox_node` for final compilation checks; if a textual conflict occurs, it routes to `master_integrator_node` to intelligently resolve it, and then loops back to retry the merge.
    *   `_create_qa_graph`: Executes the separated UAT logic (`uat_evaluate`). The topology dictates that if the test passes, the pipeline terminates successfully. If it fails, it routes to `qa_auditor` for diagnosis and `qa_session` for automated remediation, looping until success or reaching a hard failure limit.

### 3. `src/services/conflict_manager.py`
*   **Domain Concept**: The core intelligence for extracting and formatting Git conflicts into a structure an LLM can understand and resolve. It bridges the gap between raw Git index data and the cognitive requirements of the `master_integrator_node`.
*   **Modifications**:
    *   The `build_conflict_package` method undergoes a complete rewrite. Instead of reading the raw file with `<<<<<<< HEAD` markers, it must use the asynchronous `ProcessRunner` to execute specific Git index commands.
    *   It executes `git show :1:{file}` to extract the Base code, `git show :2:{file}` to extract the Local (Branch A) code, and `git show :3:{file}` to extract the Remote (Branch B) code.
    *   It constructs a comprehensive, highly structured Markdown prompt, injecting these three distinct code blocks cleanly, vastly improving the LLM's conflict-resolution accuracy.

### 4. `src/services/workflow.py`
*   **Domain Concept**: The master orchestrator responsible for stringing the 5 Phases together in the correct sequence. It controls the transition from parallel execution to sequential integration.
*   **Modifications**:
    *   The main execution flow (e.g., `run_cycle`) must logically launch Phase 2 (`_create_coder_graph`) in parallel for all required cycles.
    *   It must actively `await` the completion of all parallel branches, ensuring they all reach the `END` state of Phase 2.
    *   Subsequently, it invokes `_create_integration_graph` (Phase 3) sequentially for each completed branch, merging them one by one into the integration branch.
    *   Finally, if all integrations pass the global sandbox, it invokes `_create_qa_graph` (Phase 4) for the ultimate validation.

## Implementation Approach

The implementation of CYCLE02 requires a systematic approach to build the new integration logic, refine the conflict resolution strategy, and orchestrate the final execution flow. It culminates in a complete, end-to-end pipeline capable of autonomous, multi-agent software development.

1.  **State Definition (`src/state.py`)**: The implementation must begin by defining the two new critical Pydantic models: `IntegrationState` and `QaState`. These must be defined with strict typing. `IntegrationState` must include fields for tracking the target branch, merge status, and the crucial 3-Way Diff prompt package. `QaState` must include fields for tracking test results, logs, screenshot paths, and the iteration count of the QA remediation loop. These strongly typed models ensure data integrity as execution moves through the new graphs.

2.  **Conflict Manager Enhancement (`src/services/conflict_manager.py`)**: The developer must completely rewrite the `build_conflict_package` method. This is a highly technical task requiring the use of the project's asynchronous `ProcessRunner`. The method must execute `git show :1:{file}`, `:2:{file}`, and `:3:{file}` to gather the three distinct stages of the conflict. It must then format these three strings into a specific, structured Markdown template that explicitly labels the "Base", "Branch A", and "Branch B" code blocks, preparing the perfect context for the Integrator LLM.

3.  **Integration Nodes (`src/nodes/integration_nodes.py`)**: The logic for the new integration nodes must be implemented. `git_merge_node` will attempt the standard Git merge command and update the state with success or conflict. `master_integrator_node` will take the structured prompt from the `ConflictManager`, invoke the LLM to generate the resolved code, and write it to the file system. Finally, `global_sandbox_node` will run the project's linters and tests to ensure the merged code compiles and functions structurally.

4.  **Graph Construction (`src/graph.py`)**: With the state and nodes ready, the developer must construct `_create_integration_graph`. This involves wiring the edges: `START` -> `git_merge_node` -> conditional check. If conflict, route to `master_integrator_node` and loop back to retry `git_merge_node`. If success, route to `global_sandbox_node` -> `END`. The conditional logic must be rock-solid to prevent infinite integration loops.

5.  **UAT Isolation and Graph Adjustment (`src/services/uat_usecase.py` and `src/graph.py`)**: The `uat_usecase.py` logic must be adjusted to ensure it operates exclusively on the `QaState` and is entirely decoupled from the Coder Phase. The `_create_qa_graph` must be finalized, ensuring the loop (`uat_evaluate` -> `qa_auditor` -> `qa_session` -> retry `uat_evaluate`) functions correctly and terminates either upon success or a hard failure limit.

6.  **Master Orchestration (`src/services/workflow.py`)**: The final implementation step is to update the master `workflow.py` to string all 5 Phases together. The orchestrator must launch Phase 2 (Coder) in parallel, use `asyncio.gather` (or equivalent) to wait for all cycles to complete, then sequentially trigger Phase 3 (Integration) for each branch, and finally trigger Phase 4 (QA) only if Phase 3 concludes successfully. This completes the autonomous pipeline.

## Test Strategy

Testing this cycle is complex, requiring careful simulation of Git conflicts and precise orchestration of the end-to-end flow without relying on fragile external environments or live APIs. The strategy mandates heavy mocking to ensure tests are fast, deterministic, and isolated.

### Unit Testing Approach

The Unit Testing Approach is laser-focused on the highly technical `ConflictManager` service, specifically its ability to construct the 3-Way Diff package. The goal is to verify the string manipulation and command execution logic without requiring an actual, conflicted Git repository on the testing machine.

*   **Target**: The primary target is `src/services/conflict_manager.py` and its `build_conflict_package` method.
*   **Strategy**: The developer must aggressively use `@patch` or `pytest.MonkeyPatch` on the asynchronous `ProcessRunner.run_command` (or `subprocess.run`). This mocking strategy completely bypasses the real Git binary.
*   **Execution**: When `build_conflict_package` is called, the mocked subprocess must be programmed to return distinct, predefined strings for the three separate `git show` commands (e.g., returning "Base Code", "Branch A Code", and "Branch B Code"). The test assertions must rigorously verify that the returned prompt string successfully incorporates all three distinct blocks within the specified, structured Markdown format. This guarantees the LLM will receive the correct context without relying on side-effects.

### Integration Testing Approach

The Integration Testing Approach focuses on the orchestration of the two new LangGraphs: `_create_integration_graph` and `_create_qa_graph`. The strategy is to instantiate these graphs and simulate their execution paths by mocking the actual implementation nodes, proving the routing logic handles conflicts and failures correctly.

*   **Target**: The primary targets are the `_create_integration_graph` and `_create_qa_graph` functions in `src/graph.py`.
*   **Strategy**: The developer must instantiate both graphs. Crucially, the actual execution nodes (`git_merge_node`, `master_integrator_node`, `uat_evaluate`, `qa_session`) must be completely mocked to return predetermined state mutations, bypassing any real Git commands or LLM calls.
*   **Execution**:
    *   **Integration Graph**: Pass a simulated `IntegrationState` representing a Git conflict. The test must assert that the execution trace exactly hits `git_merge_node` (detects conflict) -> `master_integrator_node` (resolves) -> `git_merge_node` (retry success) -> `global_sandbox_node` -> `END`.
    *   **QA Graph**: Pass a simulated `QaState` representing a test failure. The test must assert that the trace hits `uat_evaluate` (fails) -> `qa_auditor` (diagnoses) -> `qa_session` (fixes) -> `uat_evaluate` (passes) -> `END`.
    *   **Side-Effect Rules**: These integration tests must ensure absolutely no real UI testing tools (like Playwright), real Git merges, or external API calls are executed. Any testing requiring database or persistent state setup MUST utilize Pytest fixtures that start a transaction before the test and roll it back after, ensuring lightning-fast state resets without relying on heavy external CLI cleanup commands. This ensures a stable, deterministic CI environment.