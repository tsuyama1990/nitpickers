# Cycle 03: Red Teaming Intra-cycle & Linter Enforcement

## 1. Summary
Cycle 03 introduces the crucial first layer of the Zero-Trust Validation mechanism: rigorous, deterministic static analysis and intra-cycle Red Teaming. Before any expensive LLM resources are used to dynamically test code in the sandbox (Cycle 04), the generated code must physically pass strict linter gates (`ruff` and `mypy`). We do not trust the AI's assertion that the code is correct; we prove it deterministically. If the code contains syntax errors, type mismatches, or formatting violations, it is immediately rejected, and the raw linter output is fed back to the Jules Coder session for correction. Following the mechanical checks, we introduce a `CoderCritic` node. This node forces the AI to pause and critically evaluate its own implementation against a strict checklist (`CODER_CRITIC_INSTRUCTION.md`), searching for logical flaws, hardcoded variables, and deviations from the interface contracts defined in Cycle 01. This cycle guarantees that only syntactically perfect, type-safe, and internally consistent code is allowed to proceed to dynamic testing.

## 2. System Architecture
This cycle heavily modifies the `coder_session` graph within `ac_cdd_core/graph.py` and `ac_cdd_core/graph_nodes.py`. We will inject a new `linter_gate_node` and a `coder_critic_node` immediately after the `coder_session_node`. The `linter_gate_node` will execute shell commands locally to run `ruff` and `mypy` against the generated files. The `coder_critic_node` will function similarly to the Architect's Self-Critic, utilizing a static prompt checklist to evaluate the code within the existing Jules session context.

### File Structure Modification
```ascii
.
├── src/
│   └── ac_cdd_core/
│       ├── **graph.py**
│       ├── **graph_nodes.py**
│       ├── **templates/CODER_CRITIC_INSTRUCTION.md**
│       └── **templates/POST_AUDIT_REFACTOR_INSTRUCTION.md**
├── pyproject.toml
└── .pre-commit-config.yaml
```

## 3. Design Architecture
The implementation hinges on capturing deterministic execution outputs and mapping them into the LangGraph state machine.

1.  **Linter Output Schema**: We need a small internal structure to capture the stdout, stderr, and exit codes of the `ruff` and `mypy` processes. If the exit code is non-zero, the execution fails.
2.  **State Update**: `CycleState` will be updated to handle `linter_feedback` (string) and `coder_critic_feedback` (string).
3.  **Prompt Engineering**: The `CODER_CRITIC_INSTRUCTION.md` must be meticulously designed. It must force the AI to execute a specific Chain of Thought (CoT), e.g., "Step 1: Verify all function signatures exactly match the SPEC.md. Step 2: Search for any hardcoded strings or magic numbers. Step 3: Ensure type hints are completely defined."
4.  **Strict Mode**: The execution of `mypy` and `ruff` must be configured (via `pyproject.toml` or CLI flags) to run in their strictest possible modes. We are aiming for zero-tolerance of sloppy code.

## 4. Implementation Approach
The implementation focuses on executing local shell commands securely and parsing their outputs into actionable feedback for the AI.

1.  **Define Instructions**: Create `CODER_CRITIC_INSTRUCTION.md` and `POST_AUDIT_REFACTOR_INSTRUCTION.md` in the templates directory. These files define the rigorous checklists for intra-cycle review and post-audit refactoring.
2.  **Implement Linter Gate**: In `src/ac_cdd_core/graph_nodes.py`, create `linter_gate_node`. This node will use Python's `subprocess` module to execute `uv run ruff check .` and `uv run mypy .` (or equivalent commands based on the project structure). Capture the output. If the return code is not 0, format the output into a string and transition the state to a failure route.
3.  **Implement Coder Critic**: Create `coder_critic_node`. This node functions like the architect critic: it loads the checklist template, formats it with the current code context, and queries the existing Jules session.
4.  **Modify the Graph**: Update `_create_coder_graph` in `src/ac_cdd_core/graph.py`. The edge from `coder_session` must now point to `linter_gate_node`. From `linter_gate_node`, conditional routing must dictate that a pass goes to `coder_critic_node`, and a fail routes back to `coder_session` with the linter feedback. From `coder_critic_node`, a pass goes to the Auditor (or UAT), and a fail routes back to `coder_session`.

## 5. Test Strategy
Testing relies heavily on executing the linters against known good and bad code samples.

**Unit Testing Approach**: We will write unit tests for the `linter_gate_node` function. We will mock the `subprocess.run` call. In one test, the mock will return an exit code of 0, and we must assert the node transitions the state to 'pass'. In another test, the mock will return an exit code of 1 with a simulated `ruff` error string. We must assert the node correctly formats this error string, appends it to the `CycleState` feedback, and transitions to 'fail'. We will similarly unit test the `coder_critic_node` by mocking the `JulesClient` responses.

**Integration Testing Approach**: We will execute a partial cycle run. We will force the mock Coder node to generate a Python file containing an obvious type error (e.g., passing a string to a function expecting an integer). We will assert that the `mypy` execution within the `linter_gate_node` correctly catches this, blocks the workflow from proceeding to the Auditor/UAT phase, and correctly funnels the exact line number and error message back into the simulated Coder session loop. This proves the physical gate functions as intended.
