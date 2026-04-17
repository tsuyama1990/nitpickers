# CYCLE05: Orchestration CLI & Workflow Service

## Summary
CYCLE05 is the final capstone, wiring the independent graphs (Architect, Coder, Integration, QA) into a unified master orchestration script. It implements the parallel execution of multiple Coder cycles followed by strict sequential integration.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
- Target Project Secrets: No new secrets.

### B. System Configurations (`docker-compose.yml`)
- No new environment variables.

### C. Sandbox Resilience
- **Mandate Mocking**: High-level workflow orchestrator tests MUST fully mock `LangGraph.invoke()` or `LangGraph.astream()` calls. Do not invoke actual graph nodes in the orchestrator unit tests.

## System Architecture

Modifications target the CLI entry points and the core workflow runner.

```text
nitpickers/
└── src/
    ├── **cli.py**
    └── services/
        └── **workflow.py**
```

## Design Architecture

- **`src/services/workflow.py` (`run_full_pipeline` or similar method)**:
  - Phase 1: Calls `build_architect_graph` to generate N cycles.
  - Phase 2: Uses `asyncio.gather` to launch `build_coder_graph` for all N cycles concurrently.
  - Phase 3: Wait for all Phase 2 futures. Proceed strictly to `build_integration_graph`.
  - Phase 4: Proceed strictly to `build_qa_graph`.
- **`src/cli.py`**:
  - Updates command structure (e.g., `run-cycle` vs `run-pipeline`) to correctly map to the new `workflow.py` logic.

## Implementation Approach

1.  Open `src/services/workflow.py`.
2.  Implement asynchronous parallel execution for Phase 2. Ensure robust error handling (e.g., `return_exceptions=True` in `asyncio.gather`).
3.  Establish strict barriers: Phase 3 MUST NOT begin until ALL Phase 2 tasks complete.
4.  Phase 4 MUST NOT begin unless Phase 3 returns a success state.
5.  Open `src/cli.py` to expose this new `run_pipeline` method safely to the user.

## Test Strategy

### Unit Testing Approach
- Use `patch` or `AsyncMock` for the graph builder functions (`build_coder_graph`, `build_integration_graph`, etc.).
- Assert that `workflow.py` calls `build_integration_graph` exactly once, and ONLY after the `asyncio.gather` for the coder graphs has resolved.

### Integration Testing Approach
- Execute the orchestrator via the CLI in a fully mocked "dry-run" mode (mocking the LLM clients) and verify the console outputs confirm the correct 5-phase sequential progression.