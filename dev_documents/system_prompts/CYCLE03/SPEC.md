# CYCLE03 Specification

## Summary
Cycle 03 establishes the formal separation of the User Acceptance Testing (UAT) Phase from the Coder Phase. Previously, UAT evaluation was entangled within the parallel Coder iterations, leading to fragmented and premature End-to-End testing. This cycle extracts the `uat_evaluate` node and its associated use cases from Phase 2 and correctly positions them within Phase 4 (QA Graph). The objective is to ensure that UAT is executed solely after the system has successfully traversed the Integration Graph (Phase 3) and passed all global structural checks. This creates a definitive, system-wide QA boundary where Playwright tests and OpenRouter vision audits can evaluate the fully integrated application as a single entity.

## Infrastructure & Dependencies
- **A. Project Secrets (`.env.example`):** The QA Phase heavily relies on OpenRouter Vision models to diagnose complex UI/UX failures. The Coder must ensure `OPENROUTER_API_KEY` is present in `.env.example` with the `# Target Project Secrets` comment.
- **B. System Configurations (`docker-compose.yml`):** Executing Playwright necessitates specific system dependencies (browsers) and potentially internal port bindings for live previews. The Coder must configure the `docker-compose.yml` environment block to explicitly support Playwright execution without disrupting the existing agent setups.
- **C. Sandbox Resilience (CRITICAL TEST STRATEGY):** *All external API calls relying on the newly defined secrets in `.env.example` (specifically the OpenRouter vision calls within the `qa_auditor` node) MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`)*. If tests attempt real network calls, the pipeline will fail, and infinite retry loops will occur during sandbox evaluation.

## System Architecture
This cycle focuses on decoupling the UAT execution from the individual Coder cycles.

**src/graph.py** (Modify)
- Remove `uat_evaluate` from `_create_coder_graph`.
- Refine the connections in `_create_qa_graph` to strictly follow the completion of Phase 3.

**src/services/uat_usecase.py** (Modify)
- Refactor the class to accept an `IntegrationState` or a specialized QA state rather than a `CycleState`, ensuring it operates on the integrated codebase.
- Remove any lingering triggers that would initiate UAT during Phase 2.

**src/nodes/qa_nodes.py** (Create/Modify)
- Implement or refine the `uat_evaluate`, `qa_auditor`, and `qa_session` nodes to operate as a self-healing loop within Phase 4.

The architecture dictates that a failure in `uat_evaluate` routes to the multimodal `qa_auditor`, which generates a fix plan, passes it to the `qa_session` for implementation, and loops back to `uat_evaluate` until the entire integrated suite passes.

## Design Architecture
The primary design adjustment is the realignment of the state input for the UAT use cases. The domain model, perhaps a new `QAExecutionState`, must extend or consume the `IntegrationState` to guarantee that the tests run against the fully merged repository. The invariants enforce that `uat_evaluate` can only trigger if the global sandbox status is strictly "pass". The `uat_evaluate` output must strictly define the path to any captured Playwright artifacts (screenshots, traces) to be consumed by the downstream `qa_auditor`. This ensures the vision models have the exact multimodal context required for accurate diagnosis. This architecture guarantees backward compatibility by isolating the UAT definitions; existing Coder logic is unaffected, as UAT is now a distinct, subsequent phase.

## Implementation Approach
1.  **Graph Decoupling:** Within `src/graph.py`, explicitly remove the `uat_evaluate` node from the Phase 2 sequence. Adjust the state typing of the graph to reflect this.
2.  **Usecase Refactoring:** Modify `src/services/uat_usecase.py`. Remove dependencies on `CycleState` and adapt the input signature to accept the finalized state from Phase 3. Ensure the core Playwright execution logic remains robust but is merely triggered at a different lifecycle stage.
3.  **QA Graph Refinement:** Ensure the Phase 4 graph correctly orchestrates the self-healing loop: `uat_evaluate` -> (on fail) -> `qa_auditor` -> `qa_session` -> `uat_evaluate`.
4.  **Sandbox Resilience Validation:** Extensively unit test the modified nodes and use cases, strictly mocking all OpenRouter API calls and Playwright browser executions to maintain a lightning-fast, resilient sandbox environment.

## Test Strategy

### Unit Testing Approach (Min 300 words)
The unit testing strategy for the decoupled UAT Phase is exceptionally crucial due to its heavy reliance on complex external systems (Playwright browsers and Vision LLMs). The Coder agent must generate comprehensive tests utilizing Pytest and `pytest-mock` to perfectly isolate the `uat_evaluate` and `qa_auditor` nodes. For `uat_evaluate`, the tests must mock the subprocess call that initiates Playwright, simulating both a successful zero-exit-code run and a failure run that outputs a predefined artifact path (e.g., a dummy screenshot file). This asserts that the node correctly parses the result and updates the state without actually spinning up headless browsers during unit evaluation. For the `qa_auditor` node, the test suite must construct a mock HTTP request to the OpenRouter API, passing in a synthetic base64-encoded image payload and verifying that the node correctly structures the returned "fix plan" JSON. This rigorous mocking strategy strictly adheres to Sandbox Resilience, guaranteeing that the unit tests can execute deterministically and swiftly without network dependencies, preventing infinite retry loops or unexpected billing surges if the logic attempts unauthorized access during testing.

### Integration Testing Approach (Min 300 words)
Integration testing for the Phase 4 graph must validate the complete self-healing loop of the UAT Phase without relying on real browsers or live API keys. The tests must construct a simulated `QAExecutionState` representing a failed E2E test, complete with a mocked artifact path. The integration test will then invoke the `_create_qa_graph`, ensuring that the workflow correctly routes from the failed `uat_evaluate` state to the `qa_auditor`. Here, the external LLM call MUST be mocked to return a successful diagnostic and a specific code modification plan. The test then traces the routing to the `qa_session` node, which applies the simulated fix, and finally loops back to the mocked `uat_evaluate` node, which must then return a simulated "pass" status. Crucially, adhering to the DB Rollback Rule, any persistent state modifications (such as generating mock artifact files) must utilize Pytest `tmp_path` fixtures, guaranteeing that the simulated UI failures do not pollute the main project directory. This end-to-end validation within a controlled, fully mocked environment confirms the structural integrity of the UAT self-healing pipeline before live execution.
