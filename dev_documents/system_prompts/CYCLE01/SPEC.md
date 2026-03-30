# CYCLE01 Specification: State Management and Coder Graph Refactoring

## Summary
The primary objective of CYCLE01 is to establish the core state control loops and thoroughly refactor the Coder Graph (`Phase 2`) so it fully integrates a strict serial auditing pipeline. Previously, the workflow lacked robust control over auditing loops, which could lead to disastrous failure modes such as infinite retries, unchecked API token consumption, or the premature integration of unpolished code.

By introducing specific, highly-typed tracking variables inside the central `src/state.py` Pydantic models and creating precisely engineered conditional routers in `src/nodes/routers.py`, we enable a deterministic, multi-stage review process (Auditor 1 -> Auditor 2 -> Auditor 3). In this new paradigm, the generated code must survive three consecutive, independent reviews before it is deemed functionally complete. Once all three auditors issue an absolute approval without caveats, the graph will conditionally trigger a mandatory `refactor_node`. The sole responsibility of this newly introduced node is to polish and clean the code, strip out temporary debugging artifacts, enforce DRY principles, and optimize the logic before it passes to final system validation. This cycle represents the crucial foundational layer that transforms the workflow from a naive generation script into a robust, zero-trust software engineering pipeline.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
This cycle focuses heavily on internal state and logic routing. No *new* external services are required beyond the existing AI providers.
However, if any external services are discovered in the target project specs during this cycle (e.g., Stripe API, SendGrid, Supabase), explicitly instruct the Coder to append these to `.env.example` with clear `# Target Project Secrets` comments. This ensures the target project can be booted cleanly.
- **Required System Secrets:**
  - `JULES_API_KEY`
  - `OPENROUTER_API_KEY`
  - `E2B_API_KEY`

### B. System Configurations (`docker-compose.yml`)
- No immediate non-confidential environmental setups are required for this cycle beyond the existing Docker configuration.
- However, if the target project specifies environmental setups (e.g., `EXECUTABLE_QE=/usr/bin/pw.x`, internal ports), instruct the Coder to place these directly into the `environment:` section of the relevant service in `docker-compose.yml`.
- Explicitly instruct the Coder to preserve valid YAML formatting and idempotency (do not overwrite existing agent configs, but safely append target project variables).

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
- **Mandate Mocking:** *All external API calls relying on the newly defined secrets in `.env.example` MUST be mocked in unit and integration tests (using `unittest.mock` or `pytest-mock`).*
- **Why:** The Sandbox will not possess the real API keys during the autonomous evaluation phase. If tests attempt real network calls to SaaS providers (like OpenAI or external databases) without valid `.env` values, the pipeline will immediately fail and cause an infinite retry loop. Testing the routing logic must not trigger real OpenRouter or Gemini API calls. The integration environment must remain entirely insulated from live networking dependencies to ensure deterministic testing.

## System Architecture

The overarching system architecture dictates that Phase 2 manages all feature implementations in isolated branches. The following file modifications are strictly required to enact the new looping controls within Phase 2. The core modifications center on the state definitions, the graph orchestrator, and the newly separated conditional routing logic.

```text
/
└── src/
    ├── **state.py**                 # Target: Add new tracking variables to CommitteeState
    ├── **graph.py**                 # Target: Rewire _create_coder_graph to include the refactor node
    └── nodes/
        └── **routers.py**           # Target: Create route_sandbox_evaluate, route_auditor, route_final_critic
```

This architecture explicitly mandates the separation of routing logic from the nodes themselves. By placing the conditional logic inside `routers.py`, we ensure that the LangGraph edge declarations in `graph.py` remain clean, declarative, and easy to read, while the complex state-evaluation logic is easily isolated and independently unit-testable. The Pydantic state models act as the absolute source of truth across all these files, guaranteeing that a node in `graph.py` perfectly aligns with the expectations of a router in `routers.py`.

The flow of data through this architecture begins at the `coder_session`, transitioning to `sandbox_evaluate`. If the sandbox passes, the state is passed to the `auditor_node`. The `auditor_node` mutates the state (adding an `AuditResult`), which the router then evaluates. Based on the `audit_attempt_count` and the `current_auditor_index`, the router directs the data back to the coder or forward to the `refactor_node`. The `refactor_node` alters the codebase and sets the `is_refactoring` flag to True, sending it back to the sandbox. Finally, the sandbox router, seeing this flag, bypasses the auditors and sends the data to the `final_critic_node`.

## Design Architecture

### Pydantic Models and Invariants
This system is strictly designed and enforced by Pydantic-based schema validation. The domain concepts represented in this cycle revolve strictly around the `CommitteeState` sub-model, which resides within the master `CycleState` class.

**Variables to Manage (`src/state.py`):**
- `is_refactoring` (`bool`): Defaults to `False`. This boolean flag is critical. It explicitly denotes whether the cycle has successfully passed the Auditor phase and is currently undergoing its final post-audit polish. If `True`, the `sandbox_evaluate` success path must route directly to the `final_critic` instead of dropping back into the `auditor` loop.
- `current_auditor_index` (`int`): Defaults to `1`. Tracks the serial progression of auditors (1, 2, 3). It represents the specific, current stage of the multi-tier review process.
- `audit_attempt_count` (`int`): Defaults to `0`. Tracks the number of times a single auditor has rejected the code. This is an essential guardrail mechanism specifically designed to prevent infinite ping-pong loops between the coder and the auditor.

**Invariants, Constraints, and Validation Rules:**
- `current_auditor_index` must be strictly typed as an integer and validated via `Field(ge=1)` to ensure it never drops below 1. The routing logic should gracefully cap it at a logical maximum (e.g., 3) and transition to a completion state.
- `audit_attempt_count` must be strictly validated via `Field(ge=0)`. It must reset to `0` when the system successfully advances to the next auditor, but it must strictly increment on each rejection from the current auditor.
- Consumers of this data will primarily be the new router functions inside `src/nodes/routers.py`. Producers of this data will be the specific action nodes like `auditor_node` (which increments counts) and `refactor_node` (which flips flags).
- Versioning and Extensibility: By locating these new integer and boolean variables within the explicit `CommitteeState` Pydantic block, backward compatibility is naturally preserved for top-level `CycleState` accessors, ensuring older test files or serialized states do not instantly break upon instantiation.

## Implementation Approach

### 1. Update `src/state.py`
The `CycleState` relies on the `CommitteeState` sub-model to handle the complex state of auditing. You must ensure that the logic robustly utilizes `is_refactoring`, `current_auditor_index`, and `audit_attempt_count` properly without violating any existing Pydantic `frozen=True` constraints. If the model is strictly frozen, ensure you utilize appropriate setter methods or completely reconstruct the model instance when mutation is strictly necessary within the node logic. These variables form the absolute backbone of the 5-phase loop control.

### 2. Implement Routing Logic (`src/nodes/routers.py`)
You must create or refine the following core conditional routing functions. These functions must be pure, relying solely on the incoming `CycleState` object to make deterministic decisions.
- `route_sandbox_evaluate(state: CycleState) -> str`:
  - If the `state.sandbox_status` explicitly equals `"failed"`, return `"failed"`.
  - If the sandbox passed AND `state.is_refactoring` exactly equals `True`, return the string `"final_critic"`.
  - Otherwise (if it passed but is not refactoring), return `"auditor"`.
- `route_auditor(state: CycleState) -> str`:
  - If `state.audit_result` indicates a rejection: increment the `audit_attempt_count`. If the attempt count strictly exceeds the predefined limits (e.g., `> 2`), trigger the fallback mechanism by returning `"reject"` (or an equivalent failure state). Otherwise, return `"reject"` to loop back to the coder.
  - If `state.audit_result` indicates an approval: increment the `current_auditor_index`. If `current_auditor_index` is strictly greater than `3` (the maximum number of auditors), return the specific signal `"pass_all"`. Otherwise, return `"next_auditor"` to trigger the next review in the chain.
- `route_final_critic(state: CycleState) -> str`:
  - Evaluate the final critic's decision. If the final critic approves the final codebase: return `"approve"`.
  - **Critical Fallback:** If the final critic unexpectedly rejects the code despite all prior checks, it must return `"reject"` to route back to `coder_session`. However, the logic must mathematically guarantee that `state.is_refactoring` is mutated back to `False` and `state.current_auditor_index` is reset to `1`. Failure to reset these variables will cause the next iteration to incorrectly bypass the auditor chain.

### 3. Rewire Coder Graph (`src/graph.py`)
You must modify `_create_coder_graph` safely and accurately to map the new routers to the correct LangGraph nodes:
- Ensure the core execution nodes (`coder_session`, `sandbox_evaluate`, `auditor_node`, `refactor_node`, `final_critic_node`) are correctly initialized and registered within the graph builder.
- Replace the existing, naive `auditor` conditional edge with the newly built `route_auditor` logic.
- Ensure the graph physically connects the `refactor_node` directly back to the `sandbox_evaluate` node to ensure the polished code is re-tested.
- Crucially, ensure the `refactor_node` logic inherently sets `state.is_refactoring = True` upon successful execution, prior to passing control back to the sandbox.

## Test Strategy

Testing this cycle is paramount. An error in the routing logic could cause catastrophic infinite loops within the live AI environment, rapidly burning through API credits. The strategy revolves around rigorous state-based unit testing combined with deterministic integration testing.

### Unit Testing Approach
- Develop comprehensive, isolated unit tests in `tests/test_routers.py`.
- You must ensure the criteria from the Design Architecture are met by manually instantiating specific, edge-case instances of `CycleState`. Systematically test different boundaries (e.g., state where `audit_attempt_count = 2` vs `3`, state where `current_auditor_index = 3` vs `4`).
- Assert with absolute certainty that `route_sandbox_evaluate`, `route_auditor`, and `route_final_critic` strictly return the exact expected routing string (e.g., `"pass_all"`, `"reject"`) without raising exceptions.
- **Mocking Strategy:** Do not attempt to spin up an entire LangGraph session or execute internal LangGraph runtime functions for these tests. Instantiate raw, mock Pydantic states and pass them into the router functions directly. This keeps the test suite lightning fast and isolates the pure logic of the routing decisions.

### Integration Testing Approach
- Develop full-path integration tests in `tests/test_coder_graph_routing.py`.
- Instantiate the actual compiled `_create_coder_graph` using the `MemorySaver` checkpointer to allow for state inspection during traversal.
- Create highly controlled mock implementations of the functional nodes (`self_critic_node`, `sandbox_evaluate_node`, `auditor_node`) using `pytest-mock` or `unittest.mock`.
- Assert that the graph traversal logic correctly enforces the 5-phase constraints. You must prove the graph mathematically transitions exactly through three auditor approvals, then successfully reaches the `refactor_node`, mutates `is_refactoring=True`, executes a successful mock sandbox run, and correctly routes to the `final_critic_node` before reaching the `END` state.
