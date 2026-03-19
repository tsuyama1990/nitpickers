# CYCLE08 UAT

## Test Scenarios

### Scenario ID: SCENARIO-08-1
**Priority**: High
This scenario validates total observability through the LangSmith UI. The user initiates a full end-to-end run of the pipeline resulting in a UAT failure and subsequent Auditor recovery. They then log into the LangSmith dashboard and visually verify the end-to-end trace, identifying explicit state mutations, accurate node routing transitions, and the exact token usage and latency of the Vision LLM call, confirming the "Black Box" has been eliminated.

### Scenario ID: SCENARIO-08-2
**Priority**: Medium
This scenario tests the serialization robustness of the state objects. The user executes the workflow ensuring that complex Pydantic objects (`UATResult`, `FixPlan`) are generated. They verify that no silent serialization errors occur during execution and that LangSmith accurately displays the JSON representation of these nested models without truncating critical paths or code snippets.

### Scenario ID: SCENARIO-08-3
**Priority**: High
This scenario tests the distinct observability of the Vision LLM calls. The user triggers the Stateless Auditor and verifies in LangSmith that the raw OpenRouter API prompt—including the Base64 encoded screenshot string—is fully logged and inspectable, ensuring prompt engineering datasets can be cleanly extracted from failed runs.

## Behavior Definitions

GIVEN a fully executing UAT pipeline triggered by the CLI
WHEN the execution successfully completes or halts
THEN LangSmith accurately captures the full node trace tree
AND the UI successfully displays the precise State dictionary mutation differences between the UAT execution node and the Auditor node natively.

GIVEN a LangGraph state containing deeply nested `FixPlan` Pydantic models
WHEN the workflow transitions between nodes
THEN the tracing layer perfectly serializes the state to JSON without throwing encoding errors
AND the full complexity of the state is visible in the LangSmith run details.

GIVEN the Stateless Auditor makes an asynchronous call to OpenRouter via LiteLLM
WHEN the call completes
THEN the global LiteLLM callback pipes the raw payload directly to LangSmith
AND the full multimodal prompt (including image data URIs) and latency metrics are explicitly recorded in the project tracing dashboard.
