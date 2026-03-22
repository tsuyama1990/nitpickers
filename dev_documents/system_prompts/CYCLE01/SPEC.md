# CYCLE01 Specification: Coder Phase & State Management Refactoring

## Summary
CYCLE01 focuses on establishing the core state management and routing logic required for the first two phases of the newly architected 5-Phase pipeline: Phase 1 (Architect Graph) and Phase 2 (Coder Graph). The primary objective is to modify the fundamental Pydantic state models—specifically the `CycleState`—to handle complex control flows, such as serial auditing loops and dedicated refactoring phases. This cycle will also rewire the LangGraph edges and conditional routing logic for the Coder Graph to enforce a zero-trust execution loop where code is generated, sandboxed, sequentially audited by multiple independent agents, and finally refactored before integration. This foundational work ensures that each cycle operates autonomously and deterministically before interacting with the broader system integration processes.

## System Architecture
This cycle targets the foundational data structures and routing mechanisms of the Coder Phase. By embedding new control variables directly into the Pydantic state, we enable LangGraph conditional edges to deterministically guide the execution flow.

### File Structure Modifications
The following files will be modified or created to support the new state and routing logic:

```text
src/
├── **state.py** (Modifying CycleState and CommitteeState)
├── **graph.py** (Rewiring _create_coder_graph)
└── nodes/
    └── **routers.py** (Implementing new conditional routing functions)
```

### Components and Interactions
1.  **State Management (`src/state.py`)**: The `CycleState` model serves as the central nervous system for a given development cycle. To support the serial auditing process and the explicit refactoring phase, we will augment the `CommitteeState` (a sub-model of `CycleState`) with new tracking variables: `is_refactoring`, `current_auditor_index`, and `audit_attempt_count`. These variables act as circuit breakers and state trackers for the LangGraph execution engine.
2.  **Graph Routing (`src/nodes/routers.py`)**: The conditional edges in LangGraph rely on routing functions that inspect the current `CycleState`. We will introduce new routers:
    -   `route_sandbox_evaluate`: Determines whether a passed sandbox evaluation should proceed to the auditor phase (if implementing) or the final critic phase (if refactoring).
    -   `route_auditor`: Manages the serial auditor loop. If an auditor rejects the code, it increments the attempt count and routes back to the coder. If approved, it moves to the next auditor in the series (1→2→3). Once all pass, it routes to the refactoring node.
    -   `route_final_critic`: Evaluates the output of the final self-critic review, routing to completion (`Approve`) or back to the coder (`Reject`).
3.  **Graph Rewiring (`src/graph.py`)**: The `_create_coder_graph` method will be updated to replace the existing parallel `committee_manager` with the new serial `auditor_node`. We will also introduce the `refactor_node` and `final_critic_node` into the execution path, wiring them together using the newly defined routers.

## Design Architecture
The NITPICKERS system is entirely driven by schema-first, Pydantic-based state management. This ensures that every transition in the LangGraph workflow is type-safe and validated.

### Domain Concepts
-   **CycleState**: Represents the entirety of a single development cycle (e.g., Phase 2). It must encapsulate all necessary context for the Coder, Sandbox, and Auditor agents.
-   **CommitteeState**: A logical grouping within `CycleState` that specifically tracks the progress of multi-agent reviews.
-   **is_refactoring (bool)**: A critical invariant. When `False`, the system is in the initial implementation phase, aiming to pass unit tests and structural checks. When `True`, the system has passed the initial checks and auditor reviews, and is now focused solely on improving code quality (e.g., readability, adherence to specific design patterns) without altering business logic.
-   **current_auditor_index (int)**: An integer (1 to 3) representing the current auditor in the series. It must increment only upon an `Approve` action.
-   **audit_attempt_count (int)**: A counter that tracks how many times a single auditor has rejected the code. This prevents infinite loops by enforcing a maximum number of retries (e.g., 2) before forcing a broader system failure or intervention.

### Invariants and Constraints
-   `current_auditor_index` must always be $\geq 1$ and $\leq$ the total number of defined auditors (e.g., 3).
-   `audit_attempt_count` must be reset to 0 when moving to a new auditor or after a successful refactoring pass, depending on the specific loop design.
-   The `CycleState` model must strictly forbid extra fields (`extra="forbid"`) to prevent silent typos from breaking the LangGraph state machine.

### Extensibility and Backward Compatibility
To maintain backward compatibility with any legacy code that interacts directly with `CycleState`, the new variables (`is_refactoring`, `current_auditor_index`, etc.) will be exposed as top-level properties on `CycleState`, even though they are logically stored within `CommitteeState` or a new dedicated sub-model. This pattern is already established in `src/state.py` using `@property` decorators.

## Implementation Approach
The implementation will follow a strict, step-by-step process prioritizing schema validation over business logic execution.

1.  **Update `src/state.py`**:
    -   Locate the `CommitteeState` Pydantic model.
    -   Add `is_refactoring: bool = Field(default=False)`.
    -   Add `audit_attempt_count: int = Field(default=0, ge=0)`.
    -   Ensure `current_auditor_index` is properly defined (it appears to exist but ensure its usage aligns with the new requirements).
    -   Update the `CycleState` properties to provide getter/setter access to these new fields for ease of use across the codebase.
    -   Run `uv run mypy src/state.py` to ensure type safety.

2.  **Implement Routers in `src/nodes/routers.py`**:
    -   Create `route_sandbox_evaluate(state: CycleState) -> str`.
        -   If `state.get("sandbox_status") == "failed"`, return `"failed"`.
        -   If `state.get("is_refactoring") == True`, return `"final_critic"`.
        -   Otherwise, return `"auditor"`.
    -   Create `route_auditor(state: CycleState) -> str`.
        -   Inspect the latest audit result (e.g., from `state.audit.audit_result.status`).
        -   If `"Reject"`, increment `state.committee.audit_attempt_count`. If it exceeds a threshold (e.g., `settings.NITPICK_MAX_ITERATIONS` or similar configuration), return `"reject"` (to a fallback node, or handle the failure). Otherwise, return `"reject"` to loop back to the coder for another attempt.
        -   If `"Approve"`, increment `state.committee.current_auditor_index`.
        -   If `state.committee.current_auditor_index > settings.NITPICK_NUM_AUDITORS` (dynamically query the configuration, do not hardcode 3), return `"pass_all"`.
        -   Otherwise, return `"next_auditor"`.
    -   Create `route_final_critic(state: CycleState) -> str`.
        -   Evaluate the self-critic result; return `"reject"` or `"approve"`.

3.  **Rewire `src/graph.py`**:
    -   Locate `_create_coder_graph`.
    -   Remove references to the parallel `committee_manager`.
    -   Add nodes: `auditor_node` (serial execution), `refactor_node`, and `final_critic_node`.
    -   Define edges using the newly created routers. Ensure the cycle flow matches the sequence: `coder_session` $\rightarrow$ `self_critic` $\rightarrow$ `sandbox_evaluate` $\rightarrow$ `route_sandbox_evaluate` $\rightarrow$ (`auditor_node` | `final_critic_node`).
    -   From `auditor_node` $\rightarrow$ `route_auditor` $\rightarrow$ (`coder_session` | `next_auditor` | `refactor_node`).
    -   From `refactor_node` $\rightarrow$ sets `state["is_refactoring"] = True` $\rightarrow$ `sandbox_evaluate`.
    -   *Crucial Enforcement*: Ensure the LLM interaction within `refactor_node` uses `pydantic-ai` or similar `litellm` capabilities to enforce structured JSON output mapping directly to the `FileOperation` schema, avoiding any raw markdown parsing vulnerabilities.

## Test Strategy

### Unit Testing Approach (Min 300 words)
The unit testing strategy for CYCLE01 will focus exclusively on validating the structural integrity of the newly introduced state models and the deterministic behavior of the routing functions, independent of any external LLM calls or complex graph execution.

First, tests will be created in `tests/test_state.py` to target the `CommitteeState` and `CycleState` models. We will instantiate these models with various permutations of the new fields (`is_refactoring`, `current_auditor_index`, `audit_attempt_count`) to verify that the Pydantic field validators enforce constraints (e.g., `audit_attempt_count` cannot be negative). We will also verify that the backward compatibility properties on `CycleState` correctly map to the underlying `CommitteeState` fields, ensuring that getting or setting these properties updates the nested state appropriately.

Second, tests will be developed for the new routing functions in `tests/nodes/test_routers.py`. We will construct dummy `CycleState` objects that mimic different points in the development cycle. For `route_sandbox_evaluate`, we will verify that a state with `sandbox_status="failed"` correctly returns `"failed"`, while a state with `is_refactoring=True` correctly returns `"final_critic"`. For `route_auditor`, we will carefully simulate the rejection loop, ensuring that returning `"Reject"` increments the attempt counter and returns `"reject"`, while returning `"Approve"` increments the auditor index and transitions to `"next_auditor"` or `"pass_all"` appropriately. These unit tests ensure that the foundational control flow logic is solid before integrating it into LangGraph.

### Integration Testing Approach (Min 300 words)
Integration testing for CYCLE01 will verify that the rewired `_create_coder_graph` operates correctly as a cohesive state machine. This involves executing the LangGraph traversal with mocked node behaviors to simulate real-world scenarios without incurring the cost or side-effects of actual LLM generation or dynamic sandbox execution.

We will write integration tests in `tests/test_coder_graph.py`. A critical test scenario will simulate a "Happy Path": starting the graph, mocking the Coder to produce code, mocking the Sandbox to pass, mocking three sequential Auditors to approve the code (verifying the `current_auditor_index` increments from 1 to 3), transitioning to the Refactor node, mocking the refactor pass (verifying `is_refactoring` becomes `True`), passing the final Sandbox evaluation, and securing approval from the Final Critic. We will assert that the final state at the `END` node correctly reflects `status="completed"` and `is_refactoring=True`.

Another crucial integration test will simulate the "Rejection Loop". We will mock an Auditor to reject the code multiple times, verifying that the graph routes back to the Coder node each time, and specifically asserting that the `audit_attempt_count` accurately reflects the number of loop iterations. Finally, we will simulate a Sandbox failure during the refactoring phase, ensuring the system correctly routes back to the Coder for remediation before attempting another final critique. These tests guarantee that the multi-phase routing logic is robust and correctly handles both successes and failures within the Coder Phase.