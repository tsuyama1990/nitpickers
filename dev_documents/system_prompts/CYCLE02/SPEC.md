# CYCLE 02: Integration Orchestration and Multi-Modal UAT Validation

## Summary
Cycle 02 focuses on orchestrating the culmination of the development process: Phase 3 (Integration Graph) and Phase 4 (QA Graph & UAT). The objective is to safely merge the parallel Coder branches using a sophisticated 3-Way Diff approach and to establish a robust, vision-assisted automated testing framework (UAT) for the final unified product. This cycle transforms the system from isolated code generation into a fully integrated and verified development pipeline. This integration must be seamless and fault-tolerant, allowing concurrent feature branches to be combined without corrupting the target project's stability. By implementing the Master Integrator with 3-Way Diff capabilities, we resolve complex merge conflicts intelligently, ensuring that the semantic intent of all branches is preserved rather than merely overwriting one set of changes with another. Furthermore, the decoupling of the UAT phase into a distinct Phase 4 validation step guarantees that visual and functional regressions are caught before final deployment. The multi-modal artifact capture mechanism provides the Vision LLM with incontrovertible evidence of UI failures, enabling precise diagnostics and automated remediation. This entire cycle acts as the final gatekeeper, enforcing the ultimate zero-trust validation before declaring a feature complete and integrated. This orchestration logic is critical for transforming the NITPICKERS tool from a mere code generator into a complete, automated software engineering pipeline capable of managing complex, multi-threaded tasks efficiently and reliably.

## Infrastructure & Dependencies
This section enforces critical separations for environment configuration and testing resilience.

### A. Project Secrets (`.env.example`)
- The UAT phase may rely on tools like Playwright which do not inherently need API keys, but the QA Auditor (Vision LLM) relies on OpenRouter.
- **Coder Instruction:** Ensure the following are present in `.env.example` under `# Target Project Secrets` if not already there:
  - `OPENROUTER_API_KEY=`
  - `E2B_API_KEY=`

### B. System Configurations (`docker-compose.yml`)
- Playwright requires system-level dependencies. The standard Nitpickers container should already provide this.
- **Coder Instruction:** Preserve existing `docker-compose.yml` configurations. Ensure no destructive changes are made to the base image setups that might break Playwright execution.

### C. Sandbox Resilience (CRITICAL TEST STRATEGY)
- **Mandate Mocking:** You MUST explicitly instruct the Coder that *all external API calls relying on the defined secrets in `.env.example` MUST be mocked in unit and integration tests*.
- *Why:* Tests asserting the functionality of the `conflict_manager` or `uat_usecase` must not execute live LLM calls or rely on a live Playwright browser connecting to the external internet in standard CI environments, as this leads to brittle, unrepeatable tests.

## System Architecture

The following files constitute the architectural blueprint for Cycle 02. These files manage the integration of disparate code branches and the execution of the final, multi-modal validation tests.

```text
src/
└── services/
    ├── **conflict_manager.py**
    │   └── (Implement complex 3-Way Diff logic for intelligent merge resolution)
    ├── **uat_usecase.py**
    │   └── (Refine artifact scanning and multi-modal schema wrapping for Playwright outputs)
    └── **workflow.py**
        └── (Enhance `run_full_pipeline` to orchestrate parallel Phase 2 execution through Phase 4)
```

This architecture explicitly separates the concerns of integration and validation. The `conflict_manager.py` is dedicated solely to Git operations and LLM prompt generation for conflict resolution. The `uat_usecase.py` acts as the bridge between raw test runner outputs and structured LangGraph state payloads. Finally, `workflow.py` serves as the high-level orchestrator, coordinating these complex, asynchronous operations into a single, cohesive, and deterministic CLI command. By maintaining these boundaries, we ensure that the integration logic remains completely isolated from the specific details of frontend testing frameworks, allowing the pipeline to scale gracefully to accommodate various technology stacks in the future.

## Design Architecture

This cycle relies heavily on rigorous path validation, concurrent execution logic via Python's `asyncio` framework, and strictly typed Pydantic models for artifact passing. The domain concepts represented here are essential for the safe and efficient merging of parallel code generation efforts. The `ConflictRegistryItem` and `MultiModalArtifact` schemas are pivotal for structuring the raw file data and test outputs into predictable formats that the LLMs can reliably process. Key invariants and constraints must be enforced programmatically to prevent directory traversal attacks and ensure that the pipeline fails fast when critical preconditions are not met.

### `src/services/conflict_manager.py`
- **Domain Concepts:** Manages Git conflict resolution by preparing context for the Master Integrator LLM. The 3-way diff methodology is central to this module, ensuring that the LLM understands the original baseline code, the changes made locally, and the changes introduced by the remote branch.
- **`build_conflict_package` Constraints:** Instead of just sending a single file littered with `<<<<<<<` markers, the system MUST utilize standard Git commands (`git show :1:file`, `:2:file`, `:3:file`) to extract the Base, Local, and Remote versions independently. This structured approach prevents the LLM from becoming confused by git syntax and focuses its attention on the semantic differences between the code versions.
- **Invariants:** Path inputs must be strictly validated to prevent directory traversal vulnerabilities. Ensure `path.resolve(strict=False).is_relative_to(...)` is used rigorously to guarantee that no file operations escape the intended workspace boundaries, adhering strictly to the security constraints outlined in the system architecture.

### `src/services/uat_usecase.py`
- **Domain Concepts:** Executes the final end-to-end tests and gathers critical diagnostic data upon failure. The UAT phase is the ultimate verification step, running code within a sandboxed environment to catch functional or visual regressions.
- **`execute` Refinement:** This method must specifically target the `QA` phase (Phase 4). When a Pytest or Playwright failure occurs, it must automatically scan a pre-configured local artifacts directory to collect evidence of the failure.
- **`MultiModalArtifact`:** It must systematically parse screenshots (`.png`) and DOM traces (`.zip`), wrapping them securely into the strictly typed `MultiModalArtifact` Pydantic schema. This structured artifact payload is then passed to the Vision LLM (e.g., via OpenRouter), providing the necessary visual context for accurate UI/UX diagnostics without raising path validation errors.

### `src/services/workflow.py`
- **Domain Concepts:** The central CLI entrypoint orchestrator. It acts as the maestro, coordinating the execution of the parallel Coder graphs, handling their synchronization, and sequentially triggering the Integration and QA phases.
- **`run_full_pipeline`:** This method must orchestrate the entire 5-phase lifecycle. First, it executes the planned Coder cycles concurrently via `AsyncDispatcher.resolve_dag()`. It must await their complete execution, aggregating their output states. Then, it triggers `build_integration_graph()` using the collected branches. Finally, if integration is successful, it triggers the QA Graph.
- **Constraints:** The orchestration must employ strict fail-fast logic. If any individual Coder phase or the Integration phase fails mechanically (e.g., due to an unresolvable conflict or a critical linter error), the entire pipeline must halt immediately, propagating the error context back to the user to prevent compounding failures downstream.

## Implementation Approach

The implementation of Cycle 02 will focus on the complex orchestration logic required to manage parallel execution, integrate concurrent changes intelligently, and safely harvest multi-modal testing artifacts. We will begin with the low-level integration mechanics in `conflict_manager.py` before moving to the UAT artifact parsing, and finally tying everything together in the high-level `workflow.py` orchestrator.

1.  **Refactor 3-Way Diff (`src/services/conflict_manager.py`)**: Substantially rewrite the `build_conflict_package` asynchronous method. Replace the naive file reading logic with `ProcessRunner` invocations. Execute `git show :1:{file}` to retrieve the common ancestor Base, `:2:{file}` for the Branch A modifications, and `:3:{file}` for the Branch B modifications. If a stage is missing (e.g., the file was newly created in one branch), gracefully handle the error and insert an appropriate placeholder. Construct the final LLM prompt string by clearly delineating these three distinct sections, providing the Master Integrator LLM with the complete historical context necessary for intelligent conflict resolution. Ensure all file paths passed to Git commands are rigorously validated against the workspace root to prevent command injection or traversal vulnerabilities.
2.  **Decouple UAT Validation (`src/services/uat_usecase.py`)**: Thoroughly review and refactor the `execute` method. Ensure the logic that handles artifact scanning (`_scan_artifacts`) is robust. Implement strict checks for file existence and apply rigorous `path.resolve().is_relative_to(...)` validation to all discovered artifact paths to prevent malicious traversal attempts. Once validated, instantiate the `MultiModalArtifact` Pydantic models with these sanitized paths. Update the conditional return statements to accurately map the internal testing outcomes to the specific string routing needs of the Phase 4 `QA Graph` (e.g., returning 'qa_auditor' if a failure occurs, or 'success' if the tests pass).
3.  **Orchestrate the Pipeline (`src/services/workflow.py`)**: This is the culmination of the 5-phase architecture. Significantly enhance the `run_full_pipeline` asynchronous method.
    -   Utilize `asyncio.gather` with `return_exceptions=True` to execute the planned cycles mapped out in Phase 1 concurrently via the `AsyncDispatcher`. Iterate through the results; if any task returns an exception, handle the failure immediately by logging the error and halting the pipeline via `sys.exit(1)`.
    -   If all Coder cycles complete successfully, aggregate the generated feature branches. Instantiate the `IntegrationState` with these branches and invoke the compiled integration graph using `build_integration_graph`. Await the result of the conflict resolution and global sandbox testing.
    -   If integration succeeds (zero exit codes from the global sandbox), proceed to instantiate a clean `CycleState` configured explicitly for Phase 4 execution. Invoke the `build_qa_graph` to run the final Playwright end-to-end tests, completing the full, automated development lifecycle.

## Test Strategy

### Unit Testing Approach (Min 300 words)
The unit testing strategy for Cycle 02 must rigorously validate the `conflict_manager.py` 3-Way Diff logic and the artifact scanning mechanisms in `uat_usecase.py`. We will construct tests that use isolated temporary directories via Pytest fixtures to simulate a genuine Git repository experiencing complex, unresolved merge conflicts. We will explicitly avoid using `unittest.mock` to stub the Git CLI invocations; instead, our fixture will initialize a bare local Git repository, create a base text file and commit it, branch off twice, create conflicting commits on both branches, and attempt a merge to intentionally generate the conflict state. We will then execute the `build_conflict_package` method asynchronously against this genuine (but isolated) repository and assert that the resulting prompt string accurately contains the distinct text blocks from the Base, Local, and Remote file versions. For the UAT phase, we will write comprehensive unit tests for the `_scan_artifacts` function. We will generate dummy `.png` screenshots and `.txt` DOM traces within a temporary artifacts directory, asserting that the method correctly discovers them, sanitizes their paths, and instantiates valid `MultiModalArtifact` Pydantic models. Crucially, we will also inject maliciously formatted paths (e.g., `../../../etc/passwd.png`) into the mock output to definitively prove that the directory traversal protections actively reject unauthorized files, ensuring the security of the pipeline during automated evaluations. We will also test the path resolution logic against symbolic links to guarantee that they cannot be exploited to access restricted directories outside the designated workspace.

### Integration Testing Approach (Min 300 words)
Integration testing will focus predominantly on the overarching orchestration logic within `src/services/workflow.py`. Given the immense complexity and duration of running genuine LLM graphs in parallel, we will test the `run_full_pipeline` method by heavily mocking the long-running underlying graph executions (`build_coder_graph`, `build_integration_graph`, `build_qa_graph`). We will utilize Python's `AsyncMock` to configure these graphs to return predetermined successful states instantly, bypassing the actual node execution logic. This isolated approach allows us to verify that the `run_full_pipeline` function correctly sequences the five phases: it awaits the completion of the parallel Coder tasks via the AsyncDispatcher, correctly aggregates and passes the necessary branch context to the Integration phase, and finally triggers the QA phase upon successful integration. We will also construct critical negative integration tests. In these tests, we will configure one of the mocked parallel Coder tasks to raise an explicit exception or return a failure state. We will then assert that the `run_full_pipeline` function correctly catches the exception, halts execution immediately, and exits with a non-zero status code rather than erroneously proceeding to the Integration phase with an incomplete or broken feature set. We will also mock an integration conflict failure to ensure the QA graph is skipped entirely under those specific conditions. This level of integration testing provides absolute confidence that the high-level orchestrator behaves predictably and safely under all possible success and failure scenarios without requiring massive computational resources to execute full LLM cycles.
