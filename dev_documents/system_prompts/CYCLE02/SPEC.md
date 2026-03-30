# CYCLE02 Specification

## Summary
CYCLE02 orchestrates the physical wiring of the 5-Phase architecture. Utilizing the robust state models and routers developed in CYCLE01, this cycle focuses on modifying the central `GraphBuilder` (`src/graph.py`) to correctly instantiate the new graphs (`_create_integration_graph`, `_create_qa_graph`, and the newly refactored `_create_coder_graph`). Concurrently, the high-level CLI entrypoints (`src/cli.py`) and the `WorkflowService` (`src/services/workflow.py`) will be overhauled to execute these graphs in their prescribed sequence: parallel Coder cycles first, followed by a singular Integration Phase, and finally, the UAT/QA validation phase. This cycle fully realizes the automated orchestration pipeline.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
-   **No new secrets are required.**
-   Explicit instruction to Coder: Do not append any new services to `.env.example` in this cycle.

### B. System Configurations (`docker-compose.yml`)
-   **No new system configurations are required.**
-   Explicit instruction to Coder: Do not modify `docker-compose.yml` in this cycle. Preserve valid YAML formatting.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
-   **Mandate Mocking:** You MUST explicitly instruct the Coder that *all external API calls relying on the defined secrets in `.env.example` MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*.
-   *Why:* The tests in this cycle verify complex graph execution flows (e.g., orchestrating multiple parallel cycles). If these tests attempt to hit the real OpenRouter or Jules endpoints, they will drastically slow down CI, consume API credits, and fail in offline environments. All LangGraph node invocations must be stubbed, allowing us to test solely the conditional branching and orchestration logic of `WorkflowService` and `GraphBuilder`.

## System Architecture

The following files represent the core components modified during this cycle:

```text
src/
├── **cli.py**                  (Entrypoints for run_cycle and run_pipeline)
├── **graph.py**                (Rewriting graph definitions for the 5 Phases)
└── services/
    ├── **workflow.py**         (Orchestrating the sequence of graphs)
    └── **uat_usecase.py**      (Isolating UAT logic for Phase 4)
```

## Design Architecture

### `src/graph.py`
The `GraphBuilder` class is responsible for physically constructing the LangGraph StateGraphs. In this cycle, its methods will be overhauled:

-   `_create_coder_graph`: This graph (Phase 2) will be rewired to support the new sequential auditor loop. Nodes will include: `coder_session`, `self_critic`, `sandbox_evaluate`, `auditor_node`, `refactor_node`, and `final_critic_node`. Conditional edges will utilize the routers developed in CYCLE01 (e.g., `route_sandbox_evaluate`, `route_auditor`).
-   `_create_integration_graph`: A entirely new graph (Phase 3) dedicated to merging branches. Nodes include: `git_merge_node`, `master_integrator_node`, and `global_sandbox_node`. It will utilize the new 3-way diff logic from CYCLE01 when conflicts occur.
-   `_create_qa_graph`: This graph (Phase 4) will be isolated. It will no longer be invoked mid-coder-cycle but solely after Phase 3 succeeds.

### `src/services/workflow.py`
The `WorkflowService` orchestrates the entire lifecycle. Currently, it might run cycles linearly or prematurely trigger UAT. The new design architecture dictates a strict phase-based execution sequence:

1.  **Phase 2 (Parallel Coder Cycles)**: The service must identify all active cycles (e.g., from `dev_documents/system_prompts/CYCLE*/SPEC.md`) and execute `build_coder_graph` for each of them *concurrently* (using `asyncio.gather`).
2.  **Phase 3 (Integration)**: Only after *all* parallel Coder cycles reach the `END` node successfully does the service invoke the `build_integration_graph` on a single, global state. If this phase fails (e.g., the `global_sandbox_node` fails to resolve an integration bug), the orchestrator must halt or trigger the `integration_fixer_node`.
3.  **Phase 4 (UAT & QA)**: Only after the `build_integration_graph` succeeds does the service invoke `build_qa_graph` to run Playwright E2E tests against the integrated codebase.

## Implementation Approach

1.  **Refactor `_create_coder_graph` in `src/graph.py`**:
    -   Remove the obsolete `committee_manager` node.
    -   Add `refactor_node` and `final_critic_node` to the workflow.
    -   Wire the edges: `START` -> `coder_session` -> `self_critic` -> `sandbox_evaluate`.
    -   Wire the conditional edge from `sandbox_evaluate` using `self.nodes.route_sandbox_evaluate`.
    -   Wire the conditional edge from `auditor` using `self.nodes.route_auditor`.
    -   Wire `refactor_node` back to `sandbox_evaluate` (ensure the node updates `state["is_refactoring"] = True`).
2.  **Implement `_create_integration_graph` in `src/graph.py`**:
    -   Create the `IntegrationState` StateGraph.
    -   Wire the edges: `START` -> `git_merge_node` -> Conditional (`route_merge`).
    -   If "conflict", route to `master_integrator_node`, then back to `git_merge_node`.
    -   If "success", route to `global_sandbox_node` -> Conditional (`route_global_sandbox`).
3.  **Refactor Orchestration in `src/services/workflow.py`**:
    -   Modify `run_pipeline` (or equivalent main entrypoint).
    -   Implement the `asyncio.gather` logic to execute all Coder cycles concurrently. Ensure robust error handling if one cycle fails while others are running.
    -   Implement the sequential handoff: Upon gathering all Coder results, instantiate the Integration graph and invoke it.
    -   Upon Integration success, instantiate the QA graph and invoke it via `src/services/uat_usecase.py`.
4.  **Isolate UAT in `src/services/uat_usecase.py`**:
    -   Remove any triggers that invoke UAT directly from the Phase 2 Coder graph. Ensure it only accepts states passed from the successful Phase 3 integration.

## Test Strategy

### Unit Testing Approach
Unit tests will focus on the `GraphBuilder`'s structural integrity. Using Pytest, we will instantiate the `GraphBuilder` with mocked services and call `_create_coder_graph`, `_create_integration_graph`, and `_create_qa_graph`. We will inspect the returned `StateGraph` objects to assert that the `.nodes` and `.edges` dictionaries contain exactly the expected keys and conditional routing functions. This ensures the graphs are physically wired according to the architectural specification without actually running them. For `uat_usecase.py`, we will verify that calling its methods with a mock state does not inadvertently trigger Phase 2 components.

### Integration Testing Approach
Integration testing will tackle the complex asynchronous orchestration in `WorkflowService`. We will mock the `CompiledStateGraph` outputs of the `GraphBuilder` to return deterministic, successful streams (`yield` mock states). The test will invoke `run_pipeline` with two mock cycles. We must assert using `unittest.mock.AsyncMock` that the `Coder Graph` was invoked twice (concurrently), the `Integration Graph` was invoked exactly once *after* both Coder graphs completed, and finally, the `QA Graph` was invoked exactly once. We will also test failure scenarios: if one Coder graph raises an exception or fails its audits, the orchestrator should gracefully halt and *not* invoke the Integration or QA graphs. All state isolation and database rollback rules apply rigorously via Pytest fixtures.