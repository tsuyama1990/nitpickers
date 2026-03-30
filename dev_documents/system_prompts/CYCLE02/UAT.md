# UAT: CYCLE02 - Integration & QA Orchestration

## Test Scenarios

This User Acceptance Testing suite validates the robustness of Phase 3 (Integration) and Phase 4 (QA) of the new 5-Phase Architecture. We must demonstrate the system's ability to seamlessly orchestrate the `Integration Graph`, intelligently resolve 3-Way Git diff conflicts, and execute the standalone `QA Graph` for multi-modal frontend validations.

As with CYCLE01, these scenarios are designed to be executed via our central `marimo` notebook (`tutorials/UAT_AND_TUTORIAL.py`). This interactive format ensures absolute transparency for the user, allowing them to witness the LLM's conflict resolution logic and the Vision Auditor's diagnostic capabilities in real-time.

### Scenario ID: UAT-C02-01 - 3-Way Diff Conflict Resolution (Mock Mode)
-   **Priority:** High
-   **Description:** This scenario validates the Master Integrator's ability to synthesize conflicting branches intelligently. The notebook will programmatically instantiate an `IntegrationState` containing a simulated Git conflict. It will bypass actual Git commands using `pytest.MonkeyPatch` and inject predefined code blocks representing the `Base` file, `Branch A`, and `Branch B`. We will execute the `_create_integration_graph` in Mock Mode. The notebook will visibly trace the route from `git_merge_node` -> `"conflict"` -> `master_integrator_node`. Crucially, the notebook must display the exact 3-Way Diff prompt payload that *would* be sent to the LLM, proving that the original architectural intent from both branches is preserved in the context window. The mock LLM will return a unified code block, and the graph will route back to `git_merge_node` -> `"success"` -> `global_sandbox_node`.

### Scenario ID: UAT-C02-02 - Multi-Modal QA Healing Loop (Live Mode)
-   **Priority:** High
-   **Description:** This scenario demonstrates the power of the decoupled Phase 4 QA Graph. The user will provide their `.env` credentials (`OPENROUTER_API_KEY`, `E2B_API_KEY`). The notebook will deploy a simple web application into the Sandbox alongside a purposefully broken Playwright test script (e.g., searching for a button that doesn't exist). We will execute `_create_qa_graph`. The notebook will capture and display the failing Playwright output, including the generated error screenshot. It will trace the routing to the `qa_auditor` (Vision LLM). The notebook will display the Vision LLM's analysis of the screenshot and its generated JSON fix plan. Finally, it will trace the routing to the `qa_session`, which will apply the fix to the test script, resulting in a successful re-evaluation at the `uat_evaluate` node.

## Behavior Definitions

These Gherkin-style definitions formalize the expected state transitions and API behaviors for the Integration and QA graphs.

**Feature:** Intelligent Branch Integration

  As a System Architect
  I want the Integration Graph to resolve Git conflicts using a 3-Way Diff
  So that the Master Integrator LLM understands the original base context and both branch intents.

  **Scenario:** Git Conflict Triggers Master Integrator
    **Given** the Integration Graph is executing
    **And** the `git_merge_node` encounters a merge conflict
    **When** the state's `unresolved_conflicts` list is populated
    **Then** the routing logic must return `"conflict"`
    **And** the graph must transition to the `master_integrator_node`.

  **Scenario:** Master Integrator Receives 3-Way Diff
    **Given** the `master_integrator_node` is preparing its LLM prompt
    **When** it requests the conflict package for a specific file
    **Then** the `ConflictManager` must extract the code via `git show :1:`, `:2:`, and `:3:`
    **And** format them into a single prompt containing `### Base`, `### Branch A`, and `### Branch B`.

  **Scenario:** Successful Integration Triggers Global Sandbox
    **Given** the Integration Graph is executing
    **When** the `git_merge_node` reports a successful, conflict-free merge
    **Then** the routing logic must return `"success"`
    **And** the graph must transition to the `global_sandbox_node` to verify the entire integrated codebase.

**Feature:** Multi-Modal QA Analysis

  As a Quality Engineer
  I want the QA Graph to analyze UI screenshots when tests fail
  So that the system can automatically diagnose and repair frontend regressions.

  **Scenario:** UAT Failure Triggers Vision Auditor
    **Given** the QA Graph is executing
    **And** the `uat_evaluate` node runs the Playwright suite
    **When** a test fails and generates an error screenshot
    **Then** the routing logic must route the state to the `qa_auditor` node
    **And** the screenshot payload must be attached to the OpenRouter Vision API request.

  **Scenario:** QA Auditor Generates Fix Plan
    **Given** the `qa_auditor` node receives a failed test state
    **When** the Vision LLM analyzes the screenshot and error logs
    **Then** it must produce a structured JSON `FixPlanSchema`
    **And** the graph must route to the `qa_session` to apply the fix.
