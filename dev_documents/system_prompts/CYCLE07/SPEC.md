# Cycle 07: Global Refactor Node

## 1. Summary
Cycle 07 introduces a post-integration optimization phase. During parallel development (Cycles 02-05), AI agents operate in isolated silos. This isolation naturally leads to code duplication—for instance, Cycle A and Cycle B might both independently implement a slightly different JSON parsing helper function. Once all concurrent cycles have successfully merged into the integration branch, the `GlobalRefactor` node performs a holistic, system-wide analysis. It evaluates the entire Abstract Syntax Tree (AST) of the assembled project against the original `SYSTEM_ARCHITECTURE.md`. Its objective is to identify and execute macro-level optimizations: consolidating duplicate logic into shared utility modules (enforcing DRY), removing circular dependencies, and purging any dead code left over from iterative refactoring. Crucially, after this global refactoring is complete, the entire codebase must be re-submitted through the complete verification pipeline (Linters and Sandbox UATs) to cryptographically prove that the structural optimizations did not alter the intended external behavior of the system.

## 2. System Architecture
This cycle adds a terminal execution phase to the overall workflow orchestration within `ac_cdd_core/services/workflow.py`. It requires creating a new `global_refactor_node` in the LangGraph structure that operates on the entire codebase context, rather than a single cycle's context.

### File Structure Modification
```ascii
.
├── src/
│   └── ac_cdd_core/
│       ├── services/
│       │   └── **workflow.py**
│       ├── **graph.py**
│       ├── **graph_nodes.py**
│       └── **templates/GLOBAL_REFACTOR_INSTRUCTION.md**
```

## 3. Design Architecture
The implementation requires defining instructions for macro-level analysis and reusing existing validation graphs.

1.  **Global Refactor Node**: This node is unique because its context window must encompass the entire `src/` directory. It uses `GLOBAL_REFACTOR_INSTRUCTION.md` to instruct Jules to look for specific anti-patterns of parallel development (duplication, orphaned files, inconsistent naming across modules).
2.  **State Management**: We will introduce a top-level state machine phase, e.g., `WorkflowPhase.GLOBAL_REFACTOR`, to distinguish this from standard cycle execution.
3.  **Verification Re-routing**: The most critical architectural decision here is that the output of `global_refactor_node` must automatically trigger the execution of the entire project validation sequence. This sequence must strictly enforce: Self-Critic Review -> Stateful Auditor Passes (2 passes x 3 auditors) -> Final Self-Critic Review -> Linter Gate -> Sandbox UAT execution. If any step fails, the pipeline must fail and route back to the refactor node with the traceback.

## 4. Implementation Approach
The implementation focuses on orchestrating a final, project-wide review and validation loop.

1.  **Define Instruction**: Create `GLOBAL_REFACTOR_INSTRUCTION.md`. This prompt must explicitly instruct the AI to perform AST-level analysis, consolidate helper functions, and enforce the DRY principle across module boundaries.
2.  **Implement Node**: In `src/graph_nodes.py`, create `global_refactor_node`. This node reads all files in `src/`, bundles them into a massive context prompt, and queries Jules. It then writes the updated files back to disk.
3.  **Modify Workflow Orchestrator**: Update `src/services/workflow.py`. Add logic so that after all pending cycles report `COMPLETED` and are merged via the Integrator, the system transitions to the `GLOBAL_REFACTOR` phase.
4.  **Re-Validation Logic**: Construct a sub-graph or sequence within `workflow.py` that executes the `ruff`/`mypy` checks against the entire project, followed by executing the complete `pytest` suite in the E2B sandbox. If any test fails, feed the error back to the `global_refactor_node`.

## 5. Test Strategy
Testing this cycle requires simulating an assembled project with intentional redundancies.

**Unit Testing Approach**: We will unit test the `global_refactor_node` formatting logic to ensure it can efficiently bundle an entire directory structure into a coherent prompt payload without exceeding token limits (though token management is primarily handled by the LLM client, we must verify the payload structure).

**Integration Testing Approach**: We will construct a dummy project workspace containing two files, `module_a.py` and `module_b.py`. Both will contain identical implementations of a complex helper function under different names. We will invoke the `global_refactor_node` via a mocked LLM that is designed to extract this function into a new `utils.py` file and update the imports. The primary assertion will verify that after the file system is modified, the re-validation pipeline is triggered, the tests (which we also provide) pass, and the final state is marked as globally optimized.
