# CYCLE04: Phase 4 UAT & QA Graph Adjustments

## Summary
CYCLE04 finalizes the isolation of the `UAT & QA Phase`. The primary task is to decouple the `uat_usecase` from the Phase 2 Coder Graph so that E2E validation only executes sequentially after Phase 3 Global Integration is fully successful.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
- Target Project Secrets:
  - No new external APIs are added; existing OpenRouter and Jules keys are reused for QA diagnostics.

### B. System Configurations (`docker-compose.yml`)
- No new environment variables needed.

### C. Sandbox Resilience
- **Mandate Mocking**: Playwright test executions and OpenRouter vision diagnostic API calls MUST be mocked when testing graph transitions to prevent CI timeouts.

## System Architecture

Modifications target the graph compilation and the UAT service entry points.

```text
nitpickers/
└── src/
    ├── **graph.py**
    └── services/
        └── **uat_usecase.py**
```

## Design Architecture

- **`src/services/uat_usecase.py`**:
  - Remove code pathways or internal triggers that previously caused it to evaluate state directly returned from the parallel Coder graph.
  - Adjust state consumption to expect the normalized output format produced by the Phase 3 `IntegrationState` completion.
- **`src/graph.py` (`_create_qa_graph`)**:
  - Keep existing logic (`uat_evaluate` -> `qa_auditor` -> `qa_session` -> `uat_evaluate`).
  - Ensure graph signature cleanly accepts a start signal decoupled from Phase 2.

## Implementation Approach

1.  Open `src/services/uat_usecase.py`. Remove any parallel cycle aggregation logic that is now obsolete due to Phase 3.
2.  Adjust type hints and state parsers in `uat_usecase.py` to interface correctly with the final aggregated state.
3.  Open `src/graph.py` and verify `_create_qa_graph` topological integrity.

## Test Strategy

### Unit Testing Approach
- Verify `uat_usecase` can instantiate and execute mock Playwright runs cleanly with basic stubbed input states.

### Integration Testing Approach
- Compile `_create_qa_graph`. Feed it a mock state. Force `uat_evaluate` to return "fail", verify it routes to `qa_auditor`, then `qa_session`, and back to `uat_evaluate` before passing.