# UAT PLAN: CYCLE 02 - Integration and UAT Orchestration

## Test Scenarios

### Scenario ID: UAT-C02-01
**Priority:** High
**Description:** Verify the automated resolution of Git conflicts using the 3-Way Diff Master Integrator.
**Context:** When concurrent cycles modify the same lines of code (e.g., adding imports to the top of a file), standard Git merges inevitably fail. The system must recognize this conflict state and invoke the Master Integrator with a comprehensive 3-way diff package to safely resolve the conflict. This scenario proves the pipeline can handle real-world development friction seamlessly, allowing parallel development to scale without bottlenecking at the integration phase.

### Scenario ID: UAT-C02-02
**Priority:** High
**Description:** Verify multi-modal artifact capture upon UAT failure.
**Context:** When a Playwright E2E test fails in Phase 4 due to an unexpected visual change or missing DOM element, the system must collect the resulting `.png` screenshots and DOM traces. It must package them correctly into a `MultiModalArtifact` schema for the Vision LLM (QA Auditor) to analyze. This scenario proves that the system captures incontrovertible evidence of UI failures, enabling precise diagnostics and automated remediation of frontend bugs without requiring human intervention.

## Behavior Definitions

### UAT-C02-01: 3-Way Diff Resolution
**GIVEN** an initialized `IntegrationState` containing feature branches with explicit, overlapping conflicting changes on the same file
**AND** the `conflict_manager` accurately detects standard `<<<<<<<` conflict markers within the target workspace
**WHEN** the `master_integrator_node` is invoked during Phase 3
**THEN** the system should generate a robust prompt package containing distinctly labeled sections for the common "Base", "Branch A" (Local), and "Branch B" (Remote) code versions
**AND** the system should successfully invoke the LLM to generate a unified, logically sound file that resolves the semantic conflict
**AND** the resulting file should be completely free of all conflict markers, allowing the `git_merge_node` to succeed on its subsequent retry.

### UAT-C02-02: Multi-Modal Capture
**GIVEN** the Phase 4 `uat_evaluate` node executes a pre-configured Playwright test suite against the integrated codebase
**AND** the test suite returns a non-zero exit code (failure) due to a simulated UI issue
**AND** the test runner deposits a `.png` screenshot and a `.txt` DOM dump in the configured local artifacts directory
**WHEN** the `uat_usecase` processes the failure state
**THEN** it should successfully and securely read the `.png` and `.txt` file paths, rejecting any path traversal attempts
**AND** it should populate the `artifacts` list within the returning `UatExecutionState` with a valid `MultiModalArtifact` Pydantic object containing the exact, sanitized absolute paths to the screenshot and trace.
