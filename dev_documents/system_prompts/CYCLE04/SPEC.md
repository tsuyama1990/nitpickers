# Cycle 04: Sandbox UAT Verification Setup

## 1. Summary
Cycle 04 constructs the second, definitive layer of the Zero-Trust Validation mechanism: execution-based verification within an isolated E2B sandbox. The system will no longer rely on the AI's assurance that the code works; it will demand physical proof in the form of successful test executions. This cycle fully implements the `uat_evaluate_node`, establishing a secure bridge between the local LangGraph orchestrator and the remote ephemeral E2B environment. The process involves synchronizing the AI-generated source code and test scripts (`pytest`) into the sandbox, executing the test commands remotely, and rigorously extracting the standard output, standard error, exit codes, and coverage reports. If the tests fail, the raw execution traceback is precisely extracted and fed back to the Jules Coder session, transforming the debugging process from a guessing game into an evidence-based resolution loop. This ensures that only code that demonstrably passes its User Acceptance Tests is permitted to merge.

## 2. System Architecture
This cycle focuses heavily on the `src/ac_cdd_core/sandbox.py` module and its integration within `ac_cdd_core/graph_nodes.py`. We will utilize the `e2b-code-interpreter` SDK to manage the remote container lifecycle. The architecture requires a seamless file synchronization mechanism to push the local project directory (or specifically, the generated `src` and `tests` directories) into the remote sandbox workspace before execution.

### File Structure Modification
```ascii
.
├── src/
│   └── ac_cdd_core/
│       ├── **sandbox.py**
│       ├── **graph_nodes.py**
│       └── **state.py**
```

## 3. Design Architecture
The design requires robust encapsulation of the remote execution logic and precise state tracking for the execution artifacts.

1.  **SandboxRunner Interface**: The `SandboxRunner` class in `sandbox.py` must be significantly expanded. It requires methods for `sync_workspace(local_dir)`, `execute_command(cmd_string)`, and `extract_artifacts()`.
2.  **Execution Result Schema**: We must define a Pydantic model (e.g., `SandboxExecutionResult`) to hold the `stdout`, `stderr`, `exit_code`, and a boolean `is_success`. This model will be embedded within the `CycleState`.
3.  **Error Parsing Logic**: When `pytest` fails, it generates a verbose traceback. We need a parser logic (potentially utilizing regex or simple string manipulation) to extract the most relevant lines of the traceback to prevent flooding the LLM context window with unnecessary noise.
4.  **Security and Isolation**: The design must guarantee that the execution is strictly confined to the E2B container. No local shell commands related to testing or execution should be permitted, ensuring the host machine remains completely insulated from potentially malicious or destructive AI-generated code.

## 4. Implementation Approach
The implementation involves complex remote API interactions and careful state mapping.

1.  **Enhance SandboxRunner**: Open `src/ac_cdd_core/sandbox.py`. Implement the file upload logic using the `e2b-code-interpreter` SDK to transfer the necessary files to the container. Implement a robust `execute` method that runs commands like `pytest -v --tb=short` and captures the outputs.
2.  **Update CycleState**: Modify `src/ac_cdd_core/state.py` to include fields for `sandbox_stdout`, `sandbox_stderr`, and `sandbox_exit_code`.
3.  **Implement uat_evaluate_node**: In `src/ac_cdd_core/graph_nodes.py`, fully flesh out the `uat_evaluate_node`. This node must:
    *   Initialize the `SandboxRunner`.
    *   Sync the current cycle's source and test files.
    *   Execute the tests.
    *   Parse the results.
    *   If the exit code is non-zero, format the `stderr` and the failed `stdout` into a prompt: "Test failed with the following traceback: <traceback>. Fix the implementation."
    *   Update the `CycleState` and route either back to the `coder_session` (if failed) or to the `auditor` (if passed).
4.  **Cleanup Logic**: Ensure that the `SandboxRunner` includes robust `__aenter__` and `__aexit__` or equivalent cleanup logic to terminate the E2B session regardless of success or failure, preventing resource leaks and unnecessary billing.

## 5. Test Strategy
Testing the sandbox integration requires verifying the remote execution bridge without actually requiring an E2B API key for unit tests.

**Unit Testing Approach**: We will heavily mock the `e2b-code-interpreter` SDK. We will write unit tests for the `SandboxRunner` class, verifying that the `execute_command` method correctly formats the payload and correctly maps a mocked remote `exit_code=1` into the internal failure state. We will also unit test the error parsing logic: provide a large string containing a simulated `pytest` traceback and assert that the parser accurately extracts the specific failing line and the AssertionError message.

**Integration Testing Approach**: This is the most critical test. We require an environment variable (e.g., `E2B_API_KEY`) to be set. The integration test will instantiate a real `SandboxRunner`, push a trivial Python script and a matching `pytest` file (one designed to pass, one designed to fail) into the live E2B container. We will execute the tests remotely and assert that the LangGraph orchestrator correctly receives the successful output and the failed traceback, proving the Zero-Trust execution gate is physically operational. We will use a temporary directory for the local files to ensure clean up.
