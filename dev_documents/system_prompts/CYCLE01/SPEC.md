# SPEC: CYCLE01 - The Coder Graph & State Foundation

## Summary

This cycle is the first of two crucial phases in transitioning the Nitpickers development environment to the newly designed 5-Phase Architecture. Our primary objective in CYCLE01 is to establish a rigorous, parallelizable foundation for the coding phase (Phase 2). This requires the systemic modification of our existing state management object (`CycleState`) to support new serial auditing and refactoring feedback loops. We must introduce critical control variables, such as `is_refactoring`, `current_auditor_index`, and `audit_attempt_count`, to accurately trace the progress of the worker agent through multiple layers of automated review.

Once the state object is enriched, we will systematically rewire the LangGraph definitions governing the `coder_graph`. The existing, simplistic flow will be replaced with a robust sequence: from the initial `coder_session`, to a preliminary `self_critic`, then into the `sandbox_evaluate` node. Crucially, the outcome of the sandbox evaluation will dynamically route the flow either to the serial `auditor_node` (for deep structural and logic review) or to the `final_critic_node` (if a post-audit refactoring phase has concluded successfully).

This cycle heavily focuses on establishing deterministic routing logic within Pydantic-validated models, ensuring that the worker agent cannot escape the zero-trust validation blockade until all conditions are demonstrably met. The implementation must strictly adhere to our additive mindset: we are extending existing schemas and interfaces to support new capabilities, taking utmost care to preserve the integrity of legacy data access patterns to avoid breaking peripheral components.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)

The Coder Graph heavily relies on various Language Model providers and execution environments. The following external service secrets must be explicitly appended to the target project's `.env.example` file, demarcated by a `# Target Project Secrets` comment.

-   `JULES_API_KEY`: Required for the primary worker agent.
-   `OPENROUTER_API_KEY`: Required for the serial auditor and vision critic nodes.
-   `E2B_API_KEY`: Required to execute the local sandbox environments securely.

The Coder must ensure these keys are represented as empty placeholders in the example file to guide user configuration without exposing real credentials.

### B. System Configurations (`docker-compose.yml`)

The operation of the parallel cycles and the subsequent serial audits requires specific non-confidential environmental setups. The Coder must inject the following configurations directly into the `environment:` section of the relevant service within the target project's `docker-compose.yml`.

-   `NITPICK_MAX_AUDITORS=3`: Defines the number of distinct serial auditors in the loop.
-   `NITPICK_MAX_AUDIT_ATTEMPTS=2`: Defines the maximum number of times an agent can loop back from a single auditor rejection before escalating or failing.
-   `NITPICK_MAX_REFACTOR_ATTEMPTS=2`: Limits the refactoring loop.

The Coder is explicitly instructed to strictly preserve valid YAML formatting and idempotency during this operation. Existing agent configurations must not be overwritten or corrupted.

### C. Sandbox Resilience

**MANDATE MOCKING:** To guarantee sandbox resilience and prevent catastrophic CI failures, the Coder MUST explicitly instruct that all external API calls relying on the newly defined secrets in `.env.example` (such as `OPENROUTER_API_KEY`) MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`).

*Why:* The CI/CD Sandbox will not possess the real API keys during the autonomous evaluation phase. If tests attempt real network calls to SaaS providers without valid `.env` values, the pipeline will fail, potentially causing infinite retry loops. Strict mocking is the only way to validate the logic of our routing nodes and state transitions without incurring actual network overhead.

## System Architecture

This section details the exact code blueprints required for the architectural changes to the Coder Graph and State Foundation.

### File Structure Modifications

The following ASCII tree outlines the files to be created or modified in this cycle, ensuring consistency with the overall System Architecture diagram.

```text
src/
├── **state.py**                # Modification: Add CommitteeState and new root flags
├── **graph.py**                # Modification: Rewire _create_coder_graph
├── nodes/
│   └── **routers.py**          # Modification: Implement route_sandbox_evaluate, route_auditor, route_final_critic
```

## Design Architecture

The structural integrity of Nitpickers relies heavily on strict, Pydantic-based schemas. The modifications outlined below are designed as pre-implementation blueprints to guarantee robust validation and boundary enforcement.

### 1. `src/state.py` (Domain Concepts & Constraints)

The `CycleState` acts as the definitive source of truth for the LangGraph. We will extend it seamlessly by introducing a `CommitteeState` sub-model.

**Domain Concept:** The `CommitteeState` encapsulates the progress of the worker through the automated review board. It tracks which auditor is currently evaluating the code and how many times the worker has attempted to satisfy that auditor's constraints.

**Key Invariants & Validation Rules:**
-   `current_auditor_index` (int): Must be strongly typed and constrained via `ge=1`. Initialized to 1.
-   `audit_attempt_count` (int): Must be strongly typed and constrained via `ge=0`. Initialized to 0. It must increment on rejection and reset on approval to the next auditor.
-   `is_refactoring` (bool): A strict boolean flag indicating whether the system has passed the auditor chain and is now polishing the code before final validation. Initialized to `False`.

**Extensibility & Backward Compatibility:**
To ensure backward compatibility, the existing properties accessed directly on `CycleState` (e.g., `state.current_auditor_index`) will be re-mapped as `@property` getters and setters pointing to the newly encapsulated `self.committee.current_auditor_index`. This prevents breaking legacy code while modernizing the underlying schema.

### 2. `src/nodes/routers.py` (Producers & Consumers)

These routing functions consume the current `CycleState` and produce the string identifier of the next LangGraph node to execute.

**Domain Concept:** The routers enforce the business logic of the 5-Phase Architecture. They represent the "conditional edges" of the graph.

**Key Invariants & Validation Rules:**
-   `route_sandbox_evaluate(state: CycleState) -> str`:
    -   If `state.get("sandbox_status") == "failed"`, return `"failed"`.
    -   If successful and `state.get("is_refactoring") == True`, return `"final_critic"`.
    -   Otherwise, return `"auditor"`.
-   `route_auditor(state: CycleState) -> str`:
    -   If the auditor review is "Reject", increment `audit_attempt_count`. Return `"reject"` (fallback logic applies if the limit is exceeded).
    -   If the auditor review is "Approve", increment `current_auditor_index`.
    -   If `current_auditor_index > 3`, return `"pass_all"`.
    -   Otherwise, return `"next_auditor"`.
-   `route_final_critic(state: CycleState) -> str`:
    -   Return `"reject"` if the self-evaluation fails, otherwise return `"approve"`.

## Implementation Approach

The implementation will be executed systematically to ensure maximum stability.

1.  **Phase 1: State Extension (Pydantic Blueprinting)**
    -   Begin by modifying `src/state.py`. Add the necessary fields to the `CommitteeState` nested model: `is_refactoring`, `current_auditor_index`, and `audit_attempt_count`.
    -   Implement the appropriate `Field(default=..., ge=...)` constraints.
    -   Ensure that the legacy properties (`@property` accessors) are updated to point to the nested `CommitteeState` fields to maintain API compatibility.
2.  **Phase 2: Routing Logic Implementation**
    -   Open `src/nodes/routers.py` and implement the three required routing functions: `route_sandbox_evaluate`, `route_auditor`, and `route_final_critic`.
    -   Strictly adhere to the logical branching defined in the Design Architecture. Utilize the `state.get()` method to safely retrieve values and mutate the state where necessary (e.g., incrementing counters).
3.  **Phase 3: Graph Rewiring (LangGraph Execution)**
    -   Open `src/graph.py` and locate the `_create_coder_graph` method.
    -   Remove the legacy nodes (`committee_manager`, `uat_evaluate`) from this specific graph.
    -   Add the new nodes: `coder_session`, `self_critic` (if not already present), `sandbox_evaluate`, `auditor_node`, `refactor_node`, and `final_critic_node`.
    -   Define the edges according to the System Architecture diagram:
        -   Start to `coder_session`.
        -   `coder_session` to `self_critic` (first pass) or directly to `sandbox_evaluate`.
        -   Add conditional edges from `sandbox_evaluate` using `route_sandbox_evaluate`.
        -   Add conditional edges from `auditor_node` using `route_auditor`.
        -   Edge from `refactor_node` to `sandbox_evaluate`.
        -   Add conditional edges from `final_critic_node` using `route_final_critic`.

## Test Strategy

A robust test suite is critical to validate the deterministic behavior of the new Coder Graph.

### Unit Testing Approach (Min 300 words)

The primary focus of the unit tests will be to validate the strict routing logic and state management encapsulations. We must guarantee that the conditional edge functions in `src/nodes/routers.py` operate flawlessly under various state conditions.

We will write dedicated test cases for `route_sandbox_evaluate`, injecting mock `CycleState` objects with different combinations of `sandbox_status` and `is_refactoring` flags. For instance, we will assert that a state with `sandbox_status="success"` and `is_refactoring=True` deterministically routes to `"final_critic"`.

Similarly, `route_auditor` will be rigorously tested. We will simulate scenarios where an auditor rejects code, verifying that the router correctly returns `"reject"` and that the state mutation (incrementing `audit_attempt_count`) occurred as expected. We will test boundary conditions, ensuring that when `current_auditor_index` surpasses the defined maximum, the function routes to `"pass_all"`.

All state modifications, particularly the nested `CommitteeState`, must be tested to ensure the legacy `@property` getters and setters in `CycleState` remain completely functional.

### Integration Testing Approach (Min 300 words)

The integration tests will evaluate the interaction between the newly wired LangGraph nodes within the `_create_coder_graph` structure. We will compile the graph (`build_coder_graph`) and execute it using a mock Checkpointer (`MemorySaver`).

To ensure sandbox resilience and adhere strictly to the "Mandate Mocking" rule, all external LLM invocations within the node functions (e.g., `coder_session`, `auditor_node`, `refactor_node`) MUST be mocked using `pytest-mock` or `patch`. The tests will not perform real HTTP calls to OpenRouter or Jules APIs.

We will trace the execution path of the graph. For example, we will inject a mock response simulating an auditor rejection and verify the graph correctly loops back to the `coder_session`. We will then simulate a successful sandbox evaluation during the refactoring phase and verify the graph terminates at the `final_critic_node` before reaching the END state. This ensures the structural integrity of the entire serial loop without incurring any external API dependency risks.
