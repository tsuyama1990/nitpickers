# CYCLE01 Specification: Foundational State and Coder Graph Refactoring

## Summary
This document outlines the precise specifications for `CYCLE01` of the NITPICKERS 5-Phase architecture redesign. This cycle is fundamentally concerned with establishing the robust inner loops of the code generation process. We will systematically overhaul the `CycleState` definitions in `src/state.py` to utilize rigid Pydantic models, ensuring all data transitions are strongly typed and immutable. Subsequently, we will implement the complex conditional routing logic in `src/nodes/routers.py` required to manage the new serial auditing and refactoring loops. Finally, we will completely rewire the `_create_coder_graph` in `src/graph.py` to seamlessly orchestrate the newly introduced `self_critic`, `auditor_node`, `refactor_node`, and `final_critic_node`, thereby replacing the deprecated parallel committee structures. By completing this cycle, the system will possess the architectural capability to autonomously generate code, subject it to multi-stage serial review, and dynamically determine whether further implementation or structural polishing is required before declaring a task complete.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
During `CYCLE01`, the core infrastructural dependencies revolve around the LLM providers necessary for the auditing and critiquing nodes. The Coder must ensure the following variables are documented in the target project's `.env.example` file.

```dotenv
# Target Project Secrets
OPENROUTER_API_KEY="your_openrouter_api_key_here"
JULES_API_KEY="your_jules_api_key_here"
E2B_API_KEY="your_e2b_api_key_here"
```

### B. System Configurations (`docker-compose.yml`)
No new internal ports or specific non-confidential environmental setups (like `EXECUTABLE_QE`) are identified as strictly necessary for this refactoring cycle beyond what already exists for the Sandbox and standard Python environment. The Coder must preserve all valid YAML formatting and idempotency; do not overwrite existing agent configurations or volume mounts. Ensure that the core `TARGET_PROJECT_PATH` logic remains intact.

### C. Sandbox Resilience
**CRITICAL TEST STRATEGY MANDATE:** The Coder MUST explicitly mock all external API calls relying on the newly defined secrets in unit and integration tests (using `unittest.mock` or `pytest-mock`).
*Why:* The Sandbox will not possess the real API keys during the autonomous evaluation phase. If tests attempt real network calls to SaaS providers (like OpenRouter or Google/Jules) without valid `.env` values, the pipeline will definitively fail and cause an infinite retry loop, completely halting the CI process. All node executions invoking LLMs must be stubbed to return deterministic, structural JSON responses.

## System Architecture
This cycle focuses heavily on the structural definitions and internal routing of the `Coder Graph` (Phase 2) and the underlying domain state.

**File Structure Overview:**
```text
src/
├── **state.py**                 # Modification: Upgrade CycleState to Pydantic
├── **graph.py**                 # Modification: Rewire _create_coder_graph
├── nodes/
│   ├── **routers.py**           # Modification: Add route_sandbox_evaluate, route_auditor, route_final_critic
│   ├── **coder.py**             # Modification: Ensure nodes accept new Pydantic state
│   ├── **auditor.py**           # Modification: Ensure nodes accept new Pydantic state
```

### Structural Blueprints

**1. State Definitions (`src/state.py`)**
The `CycleState` must be redefined to enforce strict state transitions.

```python
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Dict

class CycleState(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, arbitrary_types_allowed=True, frozen=True)

    # Existing fields (simplified for context, retain all original necessary fields)
    task_description: str
    sandbox_status: str | None = None

    # NEW FIELDS for 5-Phase Routing
    is_refactoring: bool = Field(default=False, description="Toggles post-sandbox routing between implementation audits and final structural polish.")
    current_auditor_index: int = Field(default=1, description="Tracks the current serial auditor (1 to 3).")
    audit_attempt_count: int = Field(default=0, description="Tracks iterations with a single auditor to prevent infinite loops.")
```

**2. Graph Routing (`src/nodes/routers.py`)**
The logic for transitioning between nodes based on the newly defined state.

```python
def route_sandbox_evaluate(state: CycleState) -> str:
    """Routes execution after sandbox evaluation."""
    if state.sandbox_status == "failed":
        return "failed"  # Route back to coder_session
    if state.is_refactoring:
        return "final_critic"
    return "auditor"

def route_auditor(state: CycleState) -> str:
    """Routes execution based on serial auditor feedback."""
    # Assuming the state contains an 'auditor_feedback' field populated by the auditor_node
    # Note: Actual implementation will need to parse the specific feedback structure.
    # For blueprint purposes, we assume a method `is_rejected()` exists or logic to determine rejection.

    # Pseudo-logic:
    # if feedback indicates rejection:
    #     increment audit_attempt_count
    #     return "reject"
    # else (feedback is approve):
    #     increment current_auditor_index
    #     if current_auditor_index > 3:
    #         return "pass_all"
    #     return "next_auditor"
    pass

def route_final_critic(state: CycleState) -> str:
    """Routes execution based on final self-critic review."""
    # Pseudo-logic:
    # if self_evaluation is rejected:
    #     return "reject"
    # return "approve"
    pass
```

**3. Graph Orchestration (`src/graph.py`)**
The `_create_coder_graph` function must be refactored to utilize the new nodes and routers.

```python
from langgraph.graph import StateGraph, START, END
# ... import nodes and routers ...

def _create_coder_graph() -> StateGraph:
    workflow = StateGraph(CycleState)

    # Add Nodes
    workflow.add_node("coder_session", coder_session_node)
    workflow.add_node("self_critic", self_critic_node)
    workflow.add_node("sandbox_evaluate", sandbox_evaluate_node)
    workflow.add_node("auditor_node", serial_auditor_node)
    workflow.add_node("refactor_node", refactor_node_instruction)
    workflow.add_node("final_critic_node", final_critic_node_evaluation)

    # Define Edges
    workflow.add_edge(START, "coder_session")

    # Pseudo-logic for conditional routing from coder_session based on initialization
    # If first pass: coder_session -> self_critic -> sandbox_evaluate
    # Else: coder_session -> sandbox_evaluate
    # (Implementation detail left to Coder, likely requiring another state flag or router)

    workflow.add_conditional_edges(
        "sandbox_evaluate",
        route_sandbox_evaluate,
        {
            "failed": "coder_session",
            "auditor": "auditor_node",
            "final_critic": "final_critic_node"
        }
    )

    workflow.add_conditional_edges(
        "auditor_node",
        route_auditor,
        {
            "reject": "coder_session",
            "next_auditor": "auditor_node",
            "pass_all": "refactor_node"
        }
    )

    workflow.add_edge("refactor_node", "sandbox_evaluate") # Must set is_refactoring=True internally

    workflow.add_conditional_edges(
        "final_critic_node",
        route_final_critic,
        {
            "reject": "coder_session",
            "approve": END
        }
    )

    return workflow.compile()
```

## Design Architecture
This section details the pre-implementation design for the robust Pydantic-based schema central to this refactoring effort.

The `CycleState` model defined in `src/state.py` represents the core domain concept for this cycle. It is the single source of truth for the execution state of an individual feature implementation branch. By enforcing `frozen=True` and `strict=True`, we guarantee that the state object passed between LangGraph nodes is immutable and conforms precisely to the defined data types. This eliminates entire classes of bugs related to accidental state mutation or missing dictionary keys.

**Key Invariants and Constraints:**
1.  **Immutability**: Once a `CycleState` object is instantiated for a specific step in the graph, its attributes cannot be altered. To mutate state, a new instance must be created (or a specialized update method returning a new instance must be used), ensuring a clean, auditable trace of state changes.
2.  **Serial Auditing Loop Limit**: The `audit_attempt_count` must not exceed a predefined maximum (e.g., 2) for any single `current_auditor_index`. If this limit is breached, the routing logic must enforce a fallback mechanism to prevent endless revision cycles.
3.  **Refactoring Gate**: The `is_refactoring` flag acts as a one-way gate. Once the serial auditors have unanimously approved the implementation and the `refactor_node` is triggered, `is_refactoring` becomes `True`. The system must not transition back to the serial auditor loop; it is now strictly focused on structural polish via the `final_critic_node`.

**Consumers and Producers:**
-   **Producers:** Nodes like `auditor_node` and `sandbox_evaluate` are the primary producers of new state. They analyze the current code and environment, generating updated state objects containing evaluation results and incremented counters.
-   **Consumers:** The routing functions in `src/nodes/routers.py` act as the primary consumers, inspecting the strictly typed fields of `CycleState` to determine the execution path. The nodes themselves also consume the state to acquire the necessary context (e.g., the `task_description` or current codebase state) required to execute their specific LLM prompts or system commands.

**Extensibility Considerations:**
By utilizing Pydantic's `BaseModel`, we provide a clear path for future extensibility. New flags or complex nested structures can be added with explicit type hints and validation rules without risking the stability of existing graph logic. The use of `Field(default=...)` ensures backward compatibility if legacy execution paths do not explicitly provide the new attributes.

## Implementation Approach
The implementation of `CYCLE01` must be approached systematically to minimize disruption to the existing test suite while laying the groundwork for the new architecture.

**Step 1: Pydantic State Upgrade**
Begin by modifying `src/state.py`. Convert the existing `CycleState` representation (likely a `TypedDict` or standard class) into a strict Pydantic `BaseModel`. Introduce the `is_refactoring`, `current_auditor_index`, and `audit_attempt_count` fields with their default values. Immediately execute the `mypy` type checker to identify all locations throughout the codebase where the old dictionary-style access (`state["key"]`) is used. Systematically refactor these access patterns to use attribute access (`state.key`). This step is critical; do not proceed until `mypy` reports zero errors related to state access.

**Step 2: Implement Routing Logic**
Create the new conditional routing functions within `src/nodes/routers.py`. Implement `route_sandbox_evaluate`, strictly adhering to the logic defined in the architectural blueprint. It must prioritize `sandbox_status` failures, then evaluate the `is_refactoring` flag to select between the final critic and the auditor loop. Next, implement `route_auditor`. This function is complex; it requires inspecting the specific feedback generated by the auditor node. It must increment the appropriate counters (`audit_attempt_count` on rejection, `current_auditor_index` on approval) and determine if the final approval threshold (`pass_all`) has been reached. Finally, implement `route_final_critic`.

**Step 3: Refactor the Coder Graph**
Open `src/graph.py` and locate the `_create_coder_graph` function. Carefully remove the deprecated nodes (`committee_manager`, `uat_evaluate`). Instantiate the new required nodes (`self_critic`, `auditor_node`, `refactor_node`, `final_critic_node`). You may need to create stub implementations for these nodes in `src/nodes/coder.py` and `src/nodes/auditor.py` if they do not yet exist, ensuring they accept and return the new Pydantic `CycleState`. Finally, systematically wire the graph using `workflow.add_edge` and `workflow.add_conditional_edges`, meticulously mapping the transition strings output by your new routing functions to the correct node identifiers.

**Step 4: Verification and Node State Updates**
Ensure that the newly added nodes (e.g., `refactor_node`) correctly return a new `CycleState` instance with the necessary mutations (e.g., setting `is_refactoring=True`). Verify the entire execution flow by running a simplified simulation of the graph, ensuring that all state transitions occur as expected without infinite loops.

## Test Strategy

### Unit Testing Approach (Min 300 words)
The unit testing strategy for `CYCLE01` focuses intensely on verifying the contract constraints of the Pydantic models and the precise logic of the routing functions, completely isolated from LangGraph orchestration overhead.

1.  **State Model Validation:** Create a new test suite specifically for `src/state.py`.
    -   *Assertion:* Instantiate a `CycleState` object with minimal required parameters. Assert that `is_refactoring` is exactly `False`, `current_auditor_index` is `1`, and `audit_attempt_count` is `0`.
    -   *Assertion:* Attempt to instantiate `CycleState` with an invalid type (e.g., `is_refactoring="yes"`). Assert that Pydantic raises a `ValidationError`, confirming strict type enforcement.
    -   *Assertion:* Attempt to mutate an attribute of an instantiated `CycleState` object (e.g., `state.audit_attempt_count = 5`). Assert that a `ValidationError` or similar immutability error is raised, confirming `frozen=True`.

2.  **Router Logic Verification:** Create tests for `src/nodes/routers.py` that exhaustively cover all conditional branches.
    -   *`route_sandbox_evaluate`:*
        -   Provide a state with `sandbox_status="failed"`. Assert return is `"failed"`.
        -   Provide a state with `sandbox_status="success"` and `is_refactoring=False`. Assert return is `"auditor"`.
        -   Provide a state with `sandbox_status="success"` and `is_refactoring=True`. Assert return is `"final_critic"`.
    -   *`route_auditor`:* (Requires mocking the internal logic that parses auditor feedback)
        -   Simulate a rejection state. Assert the return is `"reject"` and verify the logic intended to increment `audit_attempt_count` behaves correctly.
        -   Simulate an approval state where `current_auditor_index` is 1 or 2. Assert return is `"next_auditor"`.
        -   Simulate an approval state where `current_auditor_index` is 3. Assert return is `"pass_all"`.

**Sandbox Resilience Rule:** None of these unit tests should execute any actual LLM queries or interact with the file system. All state inputs must be manually constructed mock objects.

### Integration Testing Approach (Min 300 words)
Integration testing for `CYCLE01` involves verifying the correct assembly and traversal of the LangGraph structure defined in `_create_coder_graph`, ensuring the nodes and routers interact correctly.

1.  **Graph Compilation:**
    -   *Assertion:* Call `_create_coder_graph()`. Assert that the function successfully returns a compiled `CompiledStateGraph` object without raising any structural definition errors or dangling edge exceptions.

2.  **Simulated Traversal (Mocked Nodes):**
    -   We must verify the cyclic execution paths without triggering real LLM API calls or slow sandbox executions. To achieve this, use `pytest-mock` to aggressively patch the node execution functions (e.g., `coder_session_node`, `sandbox_evaluate_node`) within the compiled graph scope.
    -   *Scenario 1 (Happy Path):* Configure the mock nodes to immediately return success states. Execute the graph. Assert that the execution trace follows: `coder_session` -> `sandbox_evaluate` -> `auditor_node` (x3 iterations) -> `refactor_node` -> `sandbox_evaluate` -> `final_critic_node` -> `END`.
    -   *Scenario 2 (Auditor Rejection Loop):* Configure the mock `auditor_node` to return a rejection state on the first iteration, and success on subsequent iterations. Execute the graph. Assert that the execution trace correctly loops back: `... -> auditor_node -> coder_session -> sandbox_evaluate -> auditor_node -> ...` before continuing towards the end. Verify that infinite loops are prevented by observing the graph complete within a reasonable number of steps.

**DB Rollback Rule Compliance:** If the workflow system utilizes any form of persistent state tracking (e.g., sqlite checkpoints for LangGraph) during these integration tests, standard `pytest` fixtures must be utilized to encapsulate the test execution within a database transaction, explicitly rolling it back upon completion to guarantee a clean environment for subsequent tests.