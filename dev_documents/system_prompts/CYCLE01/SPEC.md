# CYCLE01: Foundation and Coder Graph Refactoring

## Summary
The primary objective of CYCLE01 is to establish the robust foundation required for the new 5-Phase architecture. This cycle focuses strictly on Phase 0 (Initialisation), Phase 1 (Architecture), and the critical refactoring of Phase 2 (the Coder Graph). We must extend the core state management (specifically `CycleState`) to support sophisticated loop control, implement the new routing logic to handle serial auditing and refactoring, and rewire the LangGraph definitions to orchestrate this new sequence. By the end of this cycle, the system will possess a highly reliable, isolated Coder Graph capable of executing continuous improvement loops (implementation, linting, auditing, and refactoring) before marking a feature branch as complete. This establishes the prerequisite machinery for the subsequent integration and global UAT phases in CYCLE02.

## Infrastructure & Dependencies

This cycle introduces structural changes that interact with external services, specifically the OpenRouter API used for the Serial Auditor chain. It is critical to enforce the following configurations:

### A. Project Secrets (`.env.example`)
The Coder must append the following required secret to the `.env.example` file. This key is strictly required for the Auditor nodes to function during real execution.
```bash
# Target Project Secrets
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### B. System Configurations (`docker-compose.yml`)
Currently, no new non-confidential environmental setups (e.g., internal ports, specific binary paths) are explicitly required by the specifications for this phase. The Coder must preserve valid YAML formatting and idempotency (do not overwrite existing agent configs).

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
**Mandate Mocking:** The Coder MUST explicitly mock all external API calls relying on the newly defined secrets in `.env.example` (specifically `OPENROUTER_API_KEY` for the `auditor_node`) in all unit and integration tests (using `unittest.mock` or `pytest-mock`).

*Why:* The Sandbox will not possess the real API keys during the autonomous evaluation phase. If tests attempt real network calls to SaaS providers without valid `.env` values, the pipeline will fail and cause an infinite retry loop. This is a strict zero-trust requirement.


## System Architecture

This section details the exact code blueprints and structural modifications required for CYCLE01. The objective is to rewire the existing LangGraph nodes without destroying the underlying agent implementations, focusing entirely on orchestration and state. We must carefully unpick the existing, tightly coupled nodes and reconstruct them into a highly resilient, linear state machine that accurately models the complexities of an iterative development lifecycle. This means separating the concerns of code generation from the concerns of static analysis, and further separating those from the concerns of high-level architectural review. The system architecture must guarantee that no code proceeds to the final integration phase without having explicitly passed through every single step of this arduous, multi-stage validation gauntlet.

**File Structure Overview:**
```text
/
├── src/
│   ├── **state.py**               # Extend CycleState schema
│   ├── **graph.py**               # Rewire _create_coder_graph
│   ├── **nodes/routers.py**       # Implement new routing functions
│   ├── services/
│   │   ├── **workflow.py**        # Update CLI/orchestration prep
│   │   └── ...
│   └── domain_models/
│       └── **cycle_state.py**     # Ensure Pydantic alignment
├── tests/
│   ├── nitpick/
│   │   ├── unit/
│   │   │   ├── **test_routers.py** # New unit tests for routing
│   │   │   └── **test_graph.py**   # Update graph traversal tests
```

### 1. State Extension (`src/state.py` & `src/domain_models/cycle_state.py`)
We must extend the `CycleState` TypedDict/Pydantic model to include the necessary control variables for the Phase 2 loops. The current `CycleState` is insufficient for tracking the complex, multi-stage nature of the new Coder Graph. By introducing these specific control flags, we transform the state object from a simple data container into a robust finite state machine configuration object. This allows the routing logic to make deterministic decisions based purely on the current state, without needing to inspect complex message histories or infer intent.

```python
# src/state.py (or equivalent domain model)
from typing import TypedDict, Annotated
import operator

class CycleState(TypedDict):
    # ... existing fields (messages, code, sandbox_status, etc.) ...

    # New Fields for Phase 2 Routing
    is_refactoring: bool            # Default: False. Indicates post-audit cleanup phase.
    current_auditor_index: int      # Default: 1. Tracks progression (1 to 3).
    audit_attempt_count: int        # Default: 0. Prevents infinite auditor rejection loops.
```
*(Note: Ensure proper initialisation logic is present wherever `CycleState` is instantiated. It is critical that these new fields are initialized to their default values globally across the application to prevent unexpected validation errors or routing failures in legacy test suites.)*

### 2. Router Implementation (`src/nodes/routers.py`)
Implement the conditional routing logic that dictates the flow of the `_create_coder_graph`. These routing functions must be entirely stateless and deterministic. They must rely solely on the data present within the `CycleState` object passed to them. They must not perform any external API calls, read from the file system, or execute any side effects. This strict adherence to pure functional design ensures that the routing logic is easily testable, highly predictable, and completely immune to transient environmental failures.

```python
# src/nodes/routers.py
def route_sandbox_evaluate(state: CycleState) -> str:
    \"\"\"Routes after local sandbox execution.\"\"\"
    if state.get("sandbox_status") == "failed":
        return "coder_session" # Back to implementation

    if state.get("is_refactoring") is True:
        return "final_critic"  # Refactoring passed sandbox, go to final review

    return "auditor_node"      # Initial implementation passed sandbox, begin audit

def route_auditor(state: CycleState) -> str:
    \"\"\"Routes after an OpenRouter auditor review.\"\"\"
    # Logic requires inspecting the latest auditor feedback in state messages
    # Assume we have a helper to parse the latest response
    status = _extract_auditor_status(state)

    if status == "reject":
        # Increment attempt count (logic handled in node or here, but node is better for state mutation)
        return "coder_session"

    if status == "approve":
        index = state.get("current_auditor_index", 1)
        if index >= 3:
            return "pass_all"
        return "next_auditor" # Loops back to auditor_node

    return "coder_session" # Fallback

def route_final_critic(state: CycleState) -> str:
    \"\"\"Routes after the final self-critic review.\"\"\"
    status = _extract_critic_status(state)
    if status == "reject":
        return "coder_session"
    return "END"
```

### 3. Graph Rewiring (`src/graph.py`)
Reconstruct the `_create_coder_graph` to utilize the new routers and nodes. This involves completely tearing down the existing graph definition and rebuilding it from scratch using the new nodes and routing logic. We must be exceptionally careful to ensure that the string literals used for conditional edge mapping exactly match the string literals returned by the routing functions. A single typo here will result in catastrophic graph execution failures. The graph must clearly define the sequential flow from the coder, to the critic, through the sandbox, into the serial auditors, and finally through the refactoring and final review phases.

```python
# src/graph.py
from langgraph.graph import StateGraph, START, END
# ... import nodes and routers ...

def _create_coder_graph() -> StateGraph:
    workflow = StateGraph(CycleState)

    # Add Nodes
    workflow.add_node("coder_session", coder_node)
    workflow.add_node("self_critic", self_critic_node)
    workflow.add_node("sandbox_evaluate", sandbox_node)
    workflow.add_node("auditor_node", openrouter_auditor_node)
    workflow.add_node("refactor_node", refactor_node) # Must set state["is_refactoring"] = True
    workflow.add_node("final_critic_node", final_critic_node)

    # Add Edges
    workflow.add_edge(START, "coder_session")

    # Simplified logic: First time go to critic, else directly to sandbox.
    # We will use a conditional edge here if needed, or handle internally in coder_session.
    workflow.add_edge("coder_session", "self_critic")
    workflow.add_edge("self_critic", "sandbox_evaluate")

    # Conditional Routing
    workflow.add_conditional_edges(
        "sandbox_evaluate",
        route_sandbox_evaluate,
        {
            "failed": "coder_session",
            "auditor_node": "auditor_node",
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

    workflow.add_edge("refactor_node", "sandbox_evaluate")

    workflow.add_conditional_edges(
        "final_critic_node",
        route_final_critic,
        {
            "reject": "coder_session",
            "END": END
        }
    )

    return workflow.compile()
```
## Design Architecture

This system relies on robust Pydantic-based schemas to ensure data integrity across the Phase 2 pipeline. The modifications in this cycle focus on extending the `CycleState` to support complex state machine transitions.

**Domain Concept: `CycleState` Extension**
The `CycleState` represents the entirety of the context required to implement, test, and audit a single feature branch. By adding `is_refactoring`, `current_auditor_index`, and `audit_attempt_count`, we transform it from a simple data container into a state machine control object.

*   **Key Invariants & Constraints:**
    *   `is_refactoring` must strictly be a boolean. It acts as a one-way latch; once set to `True` (by the `refactor_node`), it alters the routing logic of `sandbox_evaluate` permanently for that cycle.
    *   `current_auditor_index` must be an integer (1, 2, or 3). The routing logic relies on this integer to determine if the serial audit chain is complete.
    *   `audit_attempt_count` must be an integer. It serves as a safety mechanism to prevent infinite loops if an auditor repeatedly rejects the code.
*   **Consumers and Producers:**
    *   *Producers:* The `refactor_node` mutates `is_refactoring`. The `auditor_node` mutates `current_auditor_index` and `audit_attempt_count`.
    *   *Consumers:* The routing functions (`route_sandbox_evaluate`, `route_auditor`) in `src/nodes/routers.py` consume these fields to determine the next node in the graph.
*   **Backward-Compatibility:** These fields must be initialized with default values (`False`, `1`, `0` respectively) to ensure that any existing initialisation of `CycleState` throughout the codebase (e.g., in unit tests or older CLI commands) does not fail with validation errors.


## Implementation Approach

The implementation will follow a strict sequence to ensure stability and verify routing logic before integrating the actual LLM agents. This phased approach is critical because debugging complex LangGraph routing errors is notoriously difficult when obfuscated by the unpredictable latency and variable output of live large language models. We must build and test the infrastructure iteratively.

1.  **State Extension:** Begin by modifying `src/state.py`. Add the required fields to the `CycleState` TypedDict. Ensure that wherever a new `CycleState` is instantiated (e.g., in `src/services/workflow.py` or unit tests), these fields are appropriately populated with their default values. Run `mypy` and `pytest` immediately to ensure no existing typing constraints are violated. This establishes the foundational data contract upon which the rest of the implementation depends. If the state is flawed, the entire graph will inevitably fail.
2.  **Router Implementation:** Implement the three new routing functions (`route_sandbox_evaluate`, `route_auditor`, `route_final_critic`) in `src/nodes/routers.py`. These functions should be pure, deterministic, and rely entirely on the state passed to them. Do not include any side effects or external calls within these routers. This purity is what allows us to unit test the routing logic exhaustively with a vast array of permutations, ensuring that no state combination results in an unhandled routing exception.
3.  **Graph Construction:** Modify `src/graph.py` to rebuild `_create_coder_graph`. Add the new nodes (even if they are stubbed initially) and wire them using the routing functions. Pay careful attention to the conditional edges, ensuring the string literal map perfectly matches the returns from the routing functions. A mismatch here is a silent killer that will only manifest at runtime during complex graph traversals. Use extensive logging during this phase to track the exact path the state takes through the newly constructed graph.
4.  **Node Logic Updates:** Update the actual node functions (e.g., the `auditor_node`) to mutate the new state variables. For instance, the `auditor_node` must increment the `current_auditor_index` upon approval, or increment the `audit_attempt_count` upon rejection. The `refactor_node` must set `is_refactoring` to `True`. These state mutations are the engine that drives the graph forward; without them, the graph will inevitably stall in an infinite loop. We must ensure these mutations occur exactly once per node execution, and that they are atomic and completely reliable.
5.  **Mocking and Integration Verification:** Before attempting a live run, completely mock all LLM calls within the newly wired nodes. Create a test script that feeds a dummy requirement into the graph and watch it execute. Verify that it correctly traverses the implementation phase, passes the mocked sandbox, cycles through all three mocked auditors, executes the mocked refactor step, and successfully concludes. Only when this deterministic, mocked pathway is completely error-free should we transition to live API execution.


## Test Strategy

Testing in CYCLE01 must rigorously validate the routing logic and state mutations without invoking real LLMs. We adhere strictly to the sandbox resilience policy, ensuring that the test suite is fast, deterministic, and immune to external network fluctuations or API rate limits. The core objective is to prove mathematically that the complex state machine defined by the new Coder Graph operates exactly as designed under all possible state permutations.

**Unit Testing Approach (Min 300 words):**
Unit tests must verify the deterministic behaviour of the new routing functions. Create `tests/nitpick/unit/test_routers.py`. We will utilise pytest parameterisation to construct mock `CycleState` objects representing every conceivable path through the graph. For `route_sandbox_evaluate`, we will pass states where `sandbox_status` is "failed", "passed" (with `is_refactoring=False`), and "passed" (with `is_refactoring=True`), asserting the correct string is returned. This guarantees that the core decision point after the mechanical blockade operates flawlessly. For `route_auditor`, we will mock the `_extract_auditor_status` helper and verify that it correctly routes to "next_auditor" when approved (index < 3), "pass_all" when approved (index = 3), and "coder_session" when rejected. We must also explicitly test edge cases, such as the `audit_attempt_count` exceeding its maximum limit, ensuring the system safely ejects or flags the failure rather than looping infinitely. We will also test the `CycleState` initialisation to guarantee default values are applied correctly. Crucially, all unit tests must execute instantaneously and completely offline. Any unit test that attempts to make a network call must immediately fail the CI build. This strict isolation is the only way to guarantee a reliable and fast development feedback loop.

**Integration Testing Approach (Min 300 words):**
Integration testing will focus on validating the entire `_create_coder_graph` traversal. In `tests/nitpick/unit/test_graph.py` (or a dedicated integration test file), we will compile the LangGraph and execute it using an `AsyncMock` for all agent nodes. By configuring the mock nodes to return specific state mutations (e.g., the mock sandbox returns "passed", the mock auditor increments the index), we can verify the orchestrator's ability to navigate the complex loop. We must assert that the graph successfully reaches the `refactor_node` after three mock auditor approvals, that the `is_refactoring` flag is set, and that the subsequent mock sandbox evaluation correctly routes to the `final_critic_node` and eventually `END`. This integration test serves as the ultimate proof that the individual nodes and routers are wired correctly and that the overall state machine functions as a cohesive unit. We must also test failure pathways: configure a mock auditor to reject the code and verify that the graph correctly routes back to the `coder_session` node, simulating the automated self-healing loop. This ensures the structure is sound before introducing the unpredictability of live models. All external API calls (especially OpenRouter) MUST be mocked using `patch` or `AsyncMock` to satisfy the Sandbox Resilience policy. Failure to implement these mocks will result in an immediate rejection of the pull request by the mechanical blockade.
