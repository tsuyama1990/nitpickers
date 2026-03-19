# CYCLE08 SPECIFICATION

## Summary
This final cycle implements Phase 3: The Observability Layer (LangSmith Integration). Compounding the issues of context dilution is the "Black Box" nature of complex agentic workflows. When an agent gets stuck in an infinite loop trying to fix a bug, standard console logs provide insufficient visibility into why routing decisions were made or what exact multi-modal image was sent to the Vision LLM. We will ensure the entire LangGraph orchestration layer is natively integrated with LangSmith. This provides total, transparent observability of the pipeline, visualizing complex routing, tracking absolute state snapshot mutations between every node execution (e.g., `uat_exit_code`, `current_fix_plan`), and logging raw Vision LLM prompts directly. This is the ultimate panopticon for tracing, debugging, and continuous prompt evaluation.

## System Architecture
The architecture introduces native, seamless integration with LangSmith. Because LangChain, LangGraph, and LiteLLM natively support LangSmith via standard environment variables (`LANGCHAIN_TRACING_V2=true`), the architectural code overhead is near-zero, but the observability effect is profound. The system architecture mandates that the LangGraph builder (e.g., `src/graph.py` or `src/services/workflow.py`) must be executed within an explicitly configured traced context.

The architecture strictly requires that the custom Pydantic State object (containing `current_fix_plan` and `uat_result`) is fully JSON-serializable so that the LangSmith UI can automatically compute and display the diffs detailing the exact mutation between node transitions (e.g., `coder ➔ uat ➔ auditor ➔ coder`). Furthermore, Vision LLM Prompt and Response verification relies entirely on ensuring LiteLLM is globally configured to pipe its raw traces to LangSmith, bypassing the graph's internal tracing if necessary to capture standalone API calls.

```text
/
├── src/
│   ├── **graph.py**
│   ├── **cli.py**
│   └── services/
│       └── **workflow.py**
```

## Design Architecture
The design architecture requires explicitly avoiding redundant, deeply nested tracing context managers that muddy the trace tree. Instead, the design dictates passing a unified `RunnableConfig` object mapped with an explicit `run_name`, structured tags, and metadata directly into the `.ainvoke()` or `.invoke()` methods when the LangGraph state machine is initially triggered in `workflow.py`.

For the Stateless Auditor's LiteLLM calls, callbacks (`litellm.success_callback = ['langsmith']`) must be explicitly attached in the global scope to ensure raw API payloads—including the massive Base64 encoded strings—are captured accurately outside of standard LangChain wrappers. The design ensures that `LANGCHAIN_PROJECT` is strictly respected, aggregating all UAT pipeline runs into a centralized, queryable LangSmith project for quantitative regression testing and prompt engineering.

## Implementation Approach
The implementation approach involves minor but critical configuration updates across the entry points and graph execution services.

**Step 1:** Modify `src/services/workflow.py` to instantiate a `RunnableConfig` object immediately before invoking the LangGraph. Inject project metadata, user execution tags, and ensure the `LANGCHAIN_PROJECT` variable is utilized. Pass this config directly: `await graph.ainvoke(state, config=runnable_config)`.

**Step 2:** Ensure `src/graph.py` does not artificially suppress configuration propagation to its child nodes.

**Step 3:** Attach `litellm.success_callback = ['langsmith']` globally at the very top of the entry point (`src/cli.py`) to trace all Auditor Vision LLM calls seamlessly.

**Step 4:** Review the `state.py` domain models. Ensure all custom objects (especially `UATResult` and `FixPlan`) are cleanly json-serializable natively by Pydantic's `model_dump()` so LangSmith doesn't throw serialization tracking errors during state transitions.

## Test Strategy

### Unit Testing Approach
The unit tests will use `unittest.mock.patch` to verify the configuration objects. We will verify that `RunnableConfig` is properly constructed in `workflow.py` and passed into the graph's invoke method without throwing type errors or omitting required keys. We will also assert that `litellm.success_callback` is correctly appended to the global LiteLLM configuration array during the initialization of the `cli.py` module.

### Integration Testing Approach
The integration testing approach will execute a full simulated cycle within the sandbox environment (from coding to failed UAT to auditor). Using `vcrpy` or specific HTTP mock patches, we will intercept the LangSmith tracing API calls. We will verify that the State dictionary diffs (specifically the transitions involving `uat_exit_code` and `current_fix_plan`) and the Base64 image payloads are successfully formulated in the trace payload JSON, proving that the panopticon captures every critical data point exactly as designed.
