# Cycle 06: Cascading Merge Resolutions

## 1. Summary
Cycle 06 addresses the core challenge of concurrent development: integrating independently developed branches. When multiple `feature/cycle-XX` branches attempt to merge into the integration branch simultaneously, standard text-based merge conflicts are highly probable. Rather than halting the automated pipeline and requiring human intervention, this cycle introduces a 'Master Integrator' node capable of Semantic Merge Resolution. When a Git conflict occurs, the orchestrator preserves the conflict markers. It packages the conflicting files, along with the architectural context and the specific `SPEC.md` requirements of both colliding branches, and sends them to a dedicated, stateful Jules session. This AI session analyzes the intent behind both sets of changes and rewrites the conflicting blocks into a unified, logically sound implementation. The system then strictly verifies that all conflict markers have been removed before finalizing the merge.

## 2. System Architecture
This cycle introduces a new state machine layer specifically for integration, extending `ac_cdd_core/services/workflow.py` and `ac_cdd_core/graph_nodes.py`. It requires deep interaction with the Git operational layer to detect and extract conflict states.

### File Structure Modification
```ascii
.
├── src/
│   └── ac_cdd_core/
│       ├── services/
│       │   └── **workflow.py**
│       ├── **graph.py**
│       ├── **graph_nodes.py**
│       ├── **domain_models.py**
│       ├── **utils.py**
│       └── **templates/MASTER_INTEGRATOR_INSTRUCTION.md**
```

## 3. Design Architecture
The implementation requires a robust mechanism to represent Git conflicts as Pydantic models.

1.  **ConflictRegistry Schema**: Define `ConflictRegistry` in `src/domain_models.py`. It should contain `file_path`, `conflicting_blocks` (a list of raw text strings containing the `<<<<<<<` to `>>>>>>>` blocks), and `resolution_status`.
2.  **Git Conflict Extractor**: Implement a utility function in `utils.py` that, upon a failed `git merge`, scans the repository for files containing standard Git conflict markers and populates the `ConflictRegistry`.
3.  **Master Integrator Node**: Create a new node in LangGraph, `master_integrator_node`. This node uses `MASTER_INTEGRATOR_INSTRUCTION.md` to instruct a dedicated Jules session (the 'Master Integrator') to resolve the specific conflicts listed in the registry, ensuring the DRY principle is respected during the synthesis.
4.  **Marker Validation**: A strict regex-based validation step is required immediately after the integrator returns its code. If any string matching `<<<<<<<`, `=======`, or `>>>>>>>` remains in the file, the payload is instantly rejected and sent back to the integrator.

## 4. Implementation Approach
The implementation focuses on intercepting Git failures and routing them into an AI-driven resolution loop.

1.  **Define Instruction**: Create `MASTER_INTEGRATOR_INSTRUCTION.md`. This must instruct the AI to perform a semantic merge, not just a line-by-line choice. It must understand the specifications of both branches.
2.  **Implement Extractor**: In `src/utils.py`, write `extract_git_conflicts(repo_path)`. This function uses regex to find conflict markers, extracts the surrounding blocks, and returns a list of `ConflictRegistry` objects.
3.  **Modify Merge Logic**: In `src/services/workflow.py`, wrap the final `git merge` command (where the cycle branch merges into the integration branch). Catch the `subprocess.CalledProcessError` that occurs on conflict.
4.  **Implement Integrator Node**: In `src/graph_nodes.py`, build `master_integrator_node`. It reads the `ConflictRegistry`, formats the prompt, calls the AI, writes the resulting code back to the files, and crucially, runs a regex check to ensure all markers are gone.
5.  **State Machine Updates**: Ensure the state machine logic in `workflow.py` loops back to the `master_integrator_node` if the validation fails, and proceeds to `git add` and `git commit` if the resolution is verified clean.

## 5. Test Strategy
Testing relies on explicitly generating Git conflicts in a temporary repository.

**Unit Testing Approach**: We will write unit tests for the `extract_git_conflicts` utility. We will create mock files containing various complex conflict scenarios (nested blocks, multiple conflicts per file) and assert that the parser accurately extracts the blocks and populates the `ConflictRegistry` model correctly. We will also unit test the validation regex to ensure it correctly identifies residual markers and doesn't trigger false positives on normal code syntax.

**Integration Testing Approach**: We will set up a temporary Git repository. We will create two branches that modify the exact same lines of a Python file with differing logic. We will attempt a merge to intentionally trigger a conflict. We will then invoke the `master_integrator_node` using a mocked LLM response that contains the resolved code. We will assert that the node correctly writes the file, passes the marker validation, and successfully finalizes the Git merge commit without manual intervention. We will test the failure path by providing a mocked response that still contains a `=======` marker, asserting that the loop correctly catches it and retries.
