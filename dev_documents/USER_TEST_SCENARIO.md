# User Acceptance Testing & Tutorial Master Plan

## Tutorial Strategy

The primary goal of the NITPICKERS tutorials is to demonstrate the power, stability, and zero-trust validation of the newly implemented 5-Phase architecture. Tutorials must be executable, interactive, and self-documenting. To achieve this, we utilize `marimo` notebooks (`.py` files), which allow users to run Python code blocks sequentially while reading rich markdown documentation.

### Execution Modes

The tutorials must support two primary execution strategies to accommodate different user environments and CI/CD pipelines:

1.  **Mock Mode (CI / No-API-Key Execution)**:
    -   **Purpose**: To validate the structural integrity of the LangGraph routing, state management (e.g., `CycleState`), and internal system components without incurring LLM API costs or requiring external sandbox credentials (`E2B_API_KEY`, `JULES_API_KEY`, `OPENROUTER_API_KEY`).
    -   **Implementation**: The Marimo notebook will utilize a `pytest.MonkeyPatch` context or environment variable overrides to inject mock tools and mock API responses. The graphs (`_create_coder_graph`, `_create_integration_graph`, `_create_qa_graph`) will be traversed, but the actual language models will be bypassed, returning deterministic, pre-programmed responses (e.g., successful code blocks, intentional rejections to test loops).
    -   **Verification**: This mode must run flawlessly in GitHub Actions on every pull request.

2.  **Real Mode (Live API Execution)**:
    -   **Purpose**: To demonstrate the actual AI capabilities of the system, including dynamic code generation, real E2B sandbox execution, and OpenRouter Vision LLM diagnostics.
    -   **Implementation**: The tutorial will instruct the user to ensure their `.env` file is fully populated. The system will execute the real LangGraph nodes, interacting with live services.
    -   **Verification**: This mode is intended for local execution by developers or dedicated live-integration environments.

## Tutorial Plan

A **SINGLE** comprehensive Marimo notebook will be created to walk the user through the entire lifecycle of the 5-Phase pipeline.

-   **Filename**: `tutorials/UAT_AND_TUTORIAL.py`

### Notebook Structure

The `tutorials/UAT_AND_TUTORIAL.py` file will contain the following interactive sections encompassing all scenarios from CYCLE01 and CYCLE02:

1.  **Introduction & Setup (Phase 0)**:
    -   Explanation of the 5-Phase Architecture (CLI Init -> Architect -> Coder -> Integration -> UAT/QA).
    -   Environment validation cell (checking for `.env` or applying mock configurations based on a toggle).
2.  **Phase 1 & 2: The Coder Graph & Serial Auditing (CYCLE01 Scenarios)**:
    -   **Quick Start Scenario (UAT-C1-001)**: Instantiate a single `CycleState` representing a simple feature request (e.g., "Create a utility to calculate the Fibonacci sequence").
    -   Execute the `_create_coder_graph`.
    -   Observe the state transitions: The Coder generates code, the Sandbox evaluates it, and a simulated Auditor chain reviews it. The tutorial will explicitly highlight the `current_auditor_index` incrementing and the `is_refactoring` flag toggling before the final critique.
    -   **Failure Scenario (UAT-C1-002)**: Configure mock nodes to simulate a "Sandbox Failure" or "Auditor Rejection Loop", demonstrating the `audit_attempt_count` limit preventing infinite loops.
3.  **Phase 3: The Integration Graph & 3-Way Diff (CYCLE02 Scenarios)**:
    -   **Advanced Scenario (UAT-C2-001)**: Set up a simulated conflict state using `IntegrationState`. We will programmatically create a mock "Base", "Branch A", and "Branch B" version of a file.
    -   Execute the `ConflictManager.build_conflict_package` and show the synthesized prompt.
    -   Execute the `_create_integration_graph`.
    -   Observe the `master_integrator_node` resolving the conflict by generating a unified code block from the 3-Way Diff package.
4.  **Phase 4 & 5: UAT & QA Graph (Automated Remediation) (CYCLE02 Scenarios)**:
    -   **Advanced Scenario (UAT-C2-002)**: Introduce an intentional failure in a mock Playwright test, providing a dummy error trace string and mock image path.
    -   Execute the `_create_qa_graph`.
    -   Observe the system capturing the failure, the `qa_auditor` diagnosing the issue via structured JSON fix plan, and the `qa_session` applying the fix before passing the final validation.
5.  **Full Pipeline Orchestration**:
    -   Demonstrate the CLI entrypoint (`run-pipeline` equivalent) programmatically invoking the `WorkflowService` to run multiple cycles concurrently and integrate them sequentially.

## Tutorial Validation

The `tutorials/UAT_AND_TUTORIAL.py` file is considered a critical system test.
-   It must be executed successfully via `uv run marimo test tutorials/UAT_AND_TUTORIAL.py` during the standard CI testing suite.
-   The notebook must not rely on any global state that prevents it from running repeatedly.
-   Code blocks must use `try-except ImportError` patterns and dynamically manipulate `sys.path` if necessary to ensure it runs smoothly even if executed from different working directories.