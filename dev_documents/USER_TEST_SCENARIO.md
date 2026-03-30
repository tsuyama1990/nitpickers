# User Acceptance Testing & Tutorial Master Plan

## Tutorial Strategy

The primary goal of the NITPICKERS tutorials is to demonstrate the power, stability, and zero-trust validation of the newly implemented 5-Phase architecture. Tutorials must be executable, interactive, and self-documenting. To achieve this, we utilise `marimo` notebooks (`.py` files), which allow users to run Python code blocks sequentially while reading rich markdown documentation. The tutorial serves as the definitive User Acceptance Test (UAT) for the entire system redesign.

### Execution Modes

The tutorials must support two primary execution strategies to accommodate different user environments and CI/CD pipelines:

1.  **Mock Mode (CI / No-API-Key Execution)**:
    -   **Purpose**: To validate the structural integrity of the LangGraph routing, state management (e.g., the newly extended `CycleState`, the `IntegrationState`), and internal system components without incurring LLM API costs or requiring external sandbox credentials (`E2B_API_KEY`, `JULES_API_KEY`, `OPENROUTER_API_KEY`).
    -   **Implementation**: The Marimo notebook will utilise a `pytest.MonkeyPatch` context or environment variable overrides to inject mock tools and mock API responses. The newly refactored graphs (`_create_coder_graph`, `_create_integration_graph`, `_create_qa_graph`) will be traversed, but the actual language models will be bypassed. They will return deterministic, pre-programmed responses (e.g., successful code blocks, intentional rejections to test loops, structured JSON fix plans).
    -   **Verification**: This mode must run flawlessly in GitHub Actions on every pull request, acting as the ultimate integration test for the 5-Phase orchestration.

2.  **Real Mode (Live API Execution)**:
    -   **Purpose**: To demonstrate the actual AI capabilities of the system, including dynamic code generation, real E2B sandbox execution, and OpenRouter Vision LLM diagnostics acting within the new serial auditing and 3-Way Diff integration loops.
    -   **Implementation**: The tutorial will instruct the user to ensure their `.env` file is fully populated with all required Tier A secrets. The system will execute the real LangGraph nodes, interacting with live services.
    -   **Verification**: This mode is intended for local execution by developers or dedicated live-integration environments.

## Tutorial Plan

A **SINGLE** comprehensive Marimo notebook will be created to walk the user through the entire lifecycle of the 5-Phase pipeline, combining the verification requirements of CYCLE01 and CYCLE02.

-   **Filename**: `tutorials/UAT_AND_TUTORIAL.py`

### Notebook Structure

The `tutorials/UAT_AND_TUTORIAL.py` file will contain the following interactive sections, designed to be executed sequentially:

1.  **Introduction & Setup (Phase 0 & 1)**:
    -   Explanation of the 5-Phase Architecture (CLI Init -> Architect -> Coder -> Integration -> UAT/QA).
    -   Environment validation cell (checking for `.env` or applying mock configurations based on a toggle).
    -   Demonstration of the Architect Graph decomposing a simple `ALL_SPEC.md` requirement into two distinct cycle plans.

2.  **Phase 2: The Coder Graph & Serial Auditing (CYCLE01 Validation)**:
    -   **Quick Start Scenario**: Instantiate a single `CycleState` representing the first generated feature request (e.g., "Create a utility to calculate the Fibonacci sequence").
    -   Execute the refactored `_create_coder_graph` in Mock Mode.
    -   Observe the state transitions: The Coder generates code, the Sandbox evaluates it, and a simulated Serial Auditor chain reviews it. The tutorial must explicitly highlight the `current_auditor_index` incrementing (1 to 3) and the `is_refactoring` flag toggling to `True` before the final critique. This validates UAT-C01-01.
    -   **Error Remediation Scenario**: Inject a mock failure into the first auditor to demonstrate the graph looping back to the `coder_session` (validating UAT-C01-02).

3.  **Phase 3: The Integration Graph & 3-Way Diff (CYCLE02 Validation)**:
    -   **Advanced Scenario**: Set up a simulated conflict state using the new `ConflictPackage` schema. Programmatically create a mock "Base", "Branch A", and "Branch B" version of a file.
    -   Execute the newly created `_create_integration_graph` in Mock Mode.
    -   Observe the `master_integrator_node` resolving the conflict by generating a unified code block. The tutorial will explicitly display the exact prompt sent to the LLM, proving it consumes the structured 3-Way Diff package rather than raw Git markers. This validates UAT-C02-01.

4.  **Phase 4 & 5: UAT & QA Graph (Automated Remediation)**:
    -   **Advanced Scenario**: Introduce an intentional failure in a mock Playwright test, generating a simulated error log and screenshot.
    -   Execute the independently triggered `_create_qa_graph` in Mock Mode.
    -   Observe the system capturing the failure, the `qa_auditor` (Vision LLM mock) diagnosing the issue and returning a JSON plan, and the `qa_session` applying the fix before passing the final validation. This validates UAT-C02-02.

5.  **Full Pipeline Orchestration**:
    -   Demonstrate the CLI entrypoint (`run-pipeline` equivalent) programmatically invoking the `WorkflowService`.
    -   Show the asynchronous, concurrent execution of multiple Phase 2 cycles, followed by the strict sequential execution of Phase 3 and Phase 4. This validates UAT-C02-03.

## Tutorial Validation

The `tutorials/UAT_AND_TUTORIAL.py` file is considered a critical system test and the primary deliverable for user acceptance.

-   It must be executed successfully via `uv run marimo test tutorials/UAT_AND_TUTORIAL.py` during the standard CI testing suite.
-   The notebook must not rely on any global state that prevents it from running repeatedly. It must cleanly instantiate mock states for every section.
-   Code blocks must use `try-except ImportError` patterns and dynamically manipulate `sys.path` if necessary to ensure it runs smoothly even if executed from different working directories (e.g., supporting the Docker Sidecar execution context).