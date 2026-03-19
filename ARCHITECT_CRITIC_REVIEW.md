# Architect Critic Review

## 1. Verification of the Optimal Approach
<thought>
**Architectural Stress Test & Alternative Consideration**

*   **Phase 1: Docs-as-Tests (Pytest Orchestration):**
    *   *Current Approach:* Implementing a custom Pytest hook (`pytest_collect_file`) in `conftest.py` to parse Markdown blocks and yield custom Pytest `Item` instances.
    *   *Stress Test:* Pytest `Item` internals are highly complex and can be brittle across Pytest versions. Managing a dynamic execution namespace securely within a custom `Item` while maintaining full traceback support is notoriously difficult. If the markdown code imports local modules, the sys.path might not be resolved correctly.
    *   *Alternative:* A more robust, decoupled approach is to have a pre-processing step (or a simpler Pytest fixture/hook) that dynamically *generates* temporary standard `.py` test files from the Markdown blocks right before Pytest execution, and then simply points Pytest to that temporary directory. This leverages standard Pytest discovery and execution without reinventing the wheel.
    *   *Decision:* The current hook-based approach is elegant but risky. I will refine the architecture to utilize a more robust file-generation strategy (or a highly constrained `exec` environment heavily reliant on Pytest's `pytester` plugin design principles) to ensure stability. Let's pivot slightly to a "Parser -> Temp File -> Pytest Runner" pattern for Docs-as-Tests to guarantee isolation and standard reporting.

*   **Phase 2: Multi-Modal Capture (Playwright Integration):**
    *   *Current Approach:* A custom `pytest_runtest_makereport` hook intercepts failures, uses the Playwright `page` fixture to take a screenshot, and saves it to an `artifacts/` folder. The overarching `ProcessRunner` (via `uat_usecase.py`) then scans this folder.
    *   *Stress Test:* This introduces a weak coupling. `uat_usecase.py` relies on matching timestamps or test IDs in filenames to associate a screenshot with a specific test failure. If multiple tests run concurrently (e.g., via `pytest-xdist`), this folder-scanning approach is highly prone to race conditions and mismatching artifacts.
    *   *Alternative:* The Pytest hook should not just save the file; it must generate a structured JSON report (e.g., `artifact_manifest.json`) mapping the exact Pytest node ID to the absolute paths of the generated artifacts. `uat_usecase.py` then reads this definitive manifest rather than blindly scanning a directory.
    *   *Decision:* The architecture must explicitly define a `TestReportManifest` schema for the handoff between the Sandbox Pytest execution and the `uat_usecase.py` service.

*   **Phase 3: The Auditor (OpenRouter):**
    *   *Current Approach:* `auditor_usecase.py` takes the state, calls OpenRouter, gets a JSON `FixPlanSchema`, and routes back.
    *   *Stress Test:* Vision LLMs are prone to hallucinating line numbers or failing to provide valid Git diff patches if the file is large. A raw "git merge diff" might fail to apply cleanly if the context lines are slightly off.
    *   *Alternative:* The `FixPlanSchema` should be constrained to either return a complete file replacement (for small files) or utilize AST-based replacement instructions (e.g., "replace function X with Y") rather than brittle line-number-based diffs.
    *   *Decision:* The architecture holds, but the `FixPlanSchema` design in CYCLE06 must explicitly mandate AST-level replacements or full block replacements rather than fragile line-diffs to ensure the Worker can actually apply the fix.
</thought>

### Evaluation
The overarching "Worker-Auditor-Observer" architecture utilizing LangGraph and LangSmith is the optimal, modern approach for this problem domain. It perfectly segregates the stateful, context-heavy generation loop from the stateless, diagnostic evaluation loop.

However, the specific integration mechanisms defined between the Sandbox (Pytest) and the Orchestrator (`uat_usecase.py`) in the initial architecture lacked the necessary rigidity. Relying on directory scanning for artifacts is brittle. The optimal approach requires formalizing the inter-process communication using JSON manifests mapped to Pydantic schemas.

## 2. Precision of Cycle Breakdown and Design Details

The 6-cycle breakdown logically sequences the implementation. However, the details within specific cycles need sharpening based on the stress test:

*   **CYCLE02 (Docs-as-Tests):** The specification was too vague on *how* the custom Pytest items would execute safely. The design must be updated to specify that the parser will dynamically construct temporary, isolated Python test modules from the Markdown blocks, allowing the standard Pytest runner to handle execution and traceback generation natively.
*   **CYCLE04 & CYCLE05 (Artifact Handoff):** The boundary between these cycles was poorly defined. CYCLE04 generates the artifacts, and CYCLE05 consumes them. The integration mechanism (directory scanning) was weak. We must introduce a `TestReportManifest` JSON schema in CYCLE04 that the Pytest hook writes to. In CYCLE05, `uat_usecase.py` will strictly parse this JSON manifest to reliably map failures to their specific multi-modal artifacts, eliminating race conditions.
*   **CYCLE06 (Fix Plan Application):** The `FixPlanSchema` must be refined. Requesting a raw git diff from an LLM is a known failure pattern in agentic workflows. The design must specify that the Auditor outputs Abstract Syntax Tree (AST) node replacements or complete block replacements, which the Worker can deterministically apply.

## 3. Required Adjustments

1.  **SYSTEM_ARCHITECTURE.md**: Update the Design Architecture section to explicitly include the `TestReportManifest` JSON boundary between the Sandbox and the Worker. Refine the Docs-as-Tests approach.
2.  **CYCLE02**: Update `SPEC.md` and `UAT.md` to mandate the temporary file generation strategy for Pytest orchestration.
3.  **CYCLE04**: Update `SPEC.md` and `UAT.md` to mandate the generation of a strongly-typed `artifact_manifest.json` upon test failure, rather than just saving images to a folder.
4.  **CYCLE05**: Update `SPEC.md` and `UAT.md` to explicitly state that `uat_usecase.py` parses the `artifact_manifest.json` to populate the `UatExecutionState`, replacing the brittle folder scanning logic.
5.  **CYCLE06**: Update `SPEC.md` to refine the `FixPlanSchema` to mandate structural replacement instructions (AST/Block) rather than fragile line-by-line diffs.
