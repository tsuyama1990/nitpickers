# Cycle 05: Agentic TDD Flow Implementation

## 1. Summary
Cycle 05 establishes a strict Test-Driven Development (TDD) methodology within the autonomous agent workflow, building upon the sandbox execution capabilities introduced in Cycle 04. The primary objective is to mathematically prove that the AI-generated tests are valid and capable of catching failures before any actual business logic is written. This is achieved by enforcing a 'Red-Green-Refactor' loop within the LangGraph orchestrator. Specifically, the system will instruct Jules to first write the test cases based on the `UAT.md` specification and stub out the implementation logic (e.g., using `pass` or `raise NotImplementedError`). The orchestrator then executes these tests in the sandbox. Crucially, the orchestrator *requires* this execution to fail (the 'Red' phase). If the tests pass against stubbed logic, it indicates the assertions are missing or flawed, and the AI is forced to rewrite the tests. Only upon receiving a verified failure state will the orchestrator permit the AI to proceed to the 'Green' phase (implementing the actual logic) and subsequently re-running the tests to verify success.

## 2. System Architecture
This cycle modifies the `coder_session_node` and its interaction with the `uat_evaluate_node` within `ac_cdd_core/graph.py` and `ac_cdd_core/graph_nodes.py`. We will introduce a new sub-state within the `CycleState` to track the current phase of the TDD loop (e.g., `TDDPhase.RED_PHASE`, `TDDPhase.GREEN_PHASE`).

### File Structure Modification
```ascii
.
├── src/
│   └── ac_cdd_core/
│       ├── **graph.py**
│       ├── **graph_nodes.py**
│       ├── **state.py**
│       ├── **enums.py**
│       ├── **templates/TDD_RED_INSTRUCTION.md**
│       └── **templates/TDD_GREEN_INSTRUCTION.md**
```

## 3. Design Architecture
The implementation relies on tracking the TDD state securely within LangGraph.

1.  **State Extension**: `CycleState` in `src/state.py` will be extended with a new field `tdd_phase: str`, initialized to `red`.
2.  **Enum Updates**: `src/enums.py` will include new flow statuses representing the transitions, such as `TDD_RED_SUCCESS` (meaning the test failed correctly) and `TDD_RED_FAILURE` (meaning the test erroneously passed).
3.  **Instruction Templates**: We will introduce two distinct instruction templates. `TDD_RED_INSTRUCTION.md` will explicitly direct the AI to write comprehensive tests but strictly stub the implementation. `TDD_GREEN_INSTRUCTION.md` will instruct the AI to implement the logic required to make the previously written (and failing) tests pass.

## 4. Implementation Approach
The implementation focuses on modifying the existing `coder_session_node` to act as a stateful two-step process.

1.  **Define Instructions**: Create `TDD_RED_INSTRUCTION.md` (instructing to write tests and stubbed code) and `TDD_GREEN_INSTRUCTION.md` (instructing to write the implementation) in the templates directory.
2.  **Update State & Enums**: Add the `tdd_phase` to `CycleState` and the corresponding enums.
3.  **Modify Coder Session Node**: In `src/graph_nodes.py`, modify `coder_session_node`. When the node is invoked, it must check the `tdd_phase`. If `red`, it uses `TDD_RED_INSTRUCTION.md`. If `green`, it uses `TDD_GREEN_INSTRUCTION.md`.
4.  **Implement TDD Router Logic**: Create a new routing function or modify the existing `route_uat`. If the phase is `red` and `uat_evaluate_node` returns a non-zero exit code (test failed), update the state to `green` and route back to `coder_session_node`. If the phase is `red` and `uat_evaluate_node` returns a zero exit code (test passed), the test is invalid; route back to `coder_session_node` with feedback demanding stricter assertions. If the phase is `green` and the test passes, route forward to the Auditor.
5.  **Graph Update**: Update `_create_coder_graph` in `src/graph.py` to correctly wire these new conditional edges.

## 5. Test Strategy
Testing the TDD state machine requires carefully mocked executions.

**Unit Testing Approach**: We will unit test the new routing logic heavily. We will mock the `CycleState` with `tdd_phase='red'` and simulate a sandbox execution result with `exit_code=0`. We must assert that the routing function correctly identifies this as a failure of the TDD process and routes back to the Coder for a test rewrite. Conversely, a simulated `exit_code=1` during the 'red' phase must correctly update the phase to 'green' and route back to the Coder for implementation.

**Integration Testing Approach**: We will perform a simulated run-cycle execution. The mocked Jules client will first return a file with tests but `pass` implementation. The mock sandbox will return an error (Red). The system must transition to Green and request the implementation. The mock Jules client will then return the correct implementation. The mock sandbox will return success (Green). The system must then proceed to the Auditor phase. This end-to-end test validates the entire mandatory TDD loop.
