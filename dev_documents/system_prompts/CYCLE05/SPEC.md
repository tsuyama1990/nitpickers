# CYCLE05 Specification

## Summary
Cycle 05 represents the system finalization, QA stabilization, and the final polish of the 5-Phase Architecture. This cycle is dedicated to ensuring that all previously implemented phases (Init, Architect, Coder, Integration, UAT) interact flawlessly under stress. The primary objective is to implement the comprehensive logging, LangSmith tracing, and the final deterministic gating logic that ensures absolute zero-trust validation before declaring the system development complete. This cycle will also formalize the "Mock Mode" for the Marimo interactive tutorials, ensuring the entire pipeline can be verified without API dependencies.

## Infrastructure & Dependencies
- **A. Project Secrets (`.env.example`):** The final polish involves comprehensive LangSmith observability. The Coder must ensure `LANGCHAIN_TRACING_V2`, `LANGCHAIN_API_KEY`, and `LANGCHAIN_PROJECT` exist in `.env.example` with `# Target Project Secrets` comments.
- **B. System Configurations (`docker-compose.yml`):** Ensure the `nitpick` sidecar container properly injects the `.env` file variables to enable tracing. Preserve valid YAML formatting and idempotency.
- **C. Sandbox Resilience (CRITICAL TEST STRATEGY):** *All external API calls, especially the newly implemented LangSmith tracing or final production API calls, MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*. If tests attempt real network calls to LangSmith during sandbox evaluation, the tests will hang or fail due to network isolation.

## System Architecture
This cycle focuses on the observability layer, global error handling, and the final `END` node gating.

**src/config.py** (Modify)
- Ensure robust handling of the LangSmith environment variables.

**src/services/workflow.py** (Modify)
- Implement rigorous try/except blocks to catch unhandled exceptions across all phases and gracefully shut down the orchestrator, logging the exact point of failure.

**tutorials/nitpickers_5_phase_architecture.py** (Create/Modify)
- Finalize the Marimo interactive tutorial demonstrating the "Mock Mode" (CI/no-api-key execution) vs "Real Mode" of the entire 5-Phase pipeline.

The architecture dictates that every state transition, routing decision, and internal LLM prompt/response must be fully observable through LangSmith if configured, providing total transparency into the AI's decision-making process.

## Design Architecture
The design involves configuring the global application context to seamlessly integrate tracing without polluting the core domain logic. The invariants enforce that if `LANGCHAIN_TRACING_V2` is false or missing, the system must not attempt to initialize or call any LangSmith specific functions, preventing unnecessary runtime overhead. The consumers of this tracing data are the developers reviewing the system's performance, while the producers are the LangGraph underlying components. The `nitpickers_5_phase_architecture.py` tutorial is designed as an executable requirement document, ensuring that the theoretical architecture described in Phase 1 directly translates to verifiable behavior in Phase 5.

## Implementation Approach
1.  **Observability Integration:** Within `src/config.py` and the various entry points, ensure LangSmith environment variables are respected. If enabled, ensure the graph executions utilize the appropriate callbacks.
2.  **Global Error Handling:** Review `src/services/workflow.py` and the main CLI entry points. Implement top-level exception handling that captures the state object immediately preceding the crash and writes a detailed post-mortem log to `dev_documents/`.
3.  **Marimo Tutorial Finalization:** Create or refine `tutorials/nitpickers_5_phase_architecture.py`. Implement the complex mocking required for "Mock Mode" to demonstrate Phase 1 through Phase 4 successfully without hitting the OpenRouter or Jules APIs.
4.  **Resilience Validation:** Extensively test the mock tutorial execution using `uv run marimo test`, strictly ensuring no real API calls escape the mocked environment.

## Test Strategy

### Unit Testing Approach (Min 300 words)
The unit testing strategy for the final stabilization phase demands verifying the global error handling and observability mechanisms without genuinely connecting to LangSmith. The Coder agent must generate comprehensive tests utilizing Pytest to validate that `src/services/workflow.py` handles artificially injected exceptions gracefully. By employing `pytest-mock` to intercept the LangGraph execution, the tests must raise a mocked `ValueError` or `RuntimeError` and assert that the workflow service catches the exception, logs the correct failure information, and returns a non-zero exit status rather than crashing the Python process entirely. Furthermore, unit tests must explicitly verify the configuration logic in `src/config.py`, asserting that if `LANGCHAIN_TRACING_V2` is absent, the system does not attempt to initialize tracing components. This strict adherence to Sandbox Resilience guarantees that the unit test suite remains incredibly fast and immune to missing environment variables, satisfying the zero-trust verification objective without incurring API overhead or telemetry pollution.

### Integration Testing Approach (Min 300 words)
Integration testing for the Phase 5 stabilization logic must validate the overarching execution of the "Mock Mode" tutorial itself. The tests must directly execute the `tutorials/nitpickers_5_phase_architecture.py` file using the `marimo test` command. The integration test will rely on the internal mock setup within the tutorial to completely isolate the Phase 1, 2, 3, and 4 executions. Crucially, adhering to the DB Rollback Rule, any persistent state modifications (such as generating mock artifact files or post-mortem logs) must utilize Pytest `tmp_path` fixtures, guaranteeing that the simulated UI failures and tutorial executions do not pollute the main project directory. The test must assert that the entire interactive notebook executes from start to finish without errors, successfully verifying the structural integrity of the LangGraph routing, state management (e.g., `CycleState`), and internal system components without incurring LLM API costs or requiring external sandbox credentials. This definitive, automated execution of the UAT master plan guarantees the final stability of the 5-Phase Architecture.
