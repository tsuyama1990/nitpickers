# CYCLE08 SPECIFICATION

## Summary
This final cycle implements Phase 3: The Observability Layer (LangSmith Integration). We will ensure the entire LangGraph orchestration layer is directly integrated with LangSmith. This provides total observability of the pipeline, visualizing complex routing and infinite loops, tracking state snapshot mutations between every node execution, and logging raw Vision LLM prompts natively.

## System Architecture
The architecture introduces native integration with LangSmith. Because LangChain and LangGraph natively support LangSmith via standard environment variables (`LANGCHAIN_TRACING_V2=true`), the architectural overhead is near-zero in implementation but profound in effect. The system architecture mandates that the LangGraph builder (e.g., `src/graph.py` or `src/services/workflow.py`) and all standalone LiteLLM calls must be executed within a traced context.

```text
/
├── src/
│   ├── **graph.py**
│   ├── **cli.py**
│   └── services/
│       └── **workflow.py**
```

## Design Architecture
The design architecture requires explicitly avoiding redundant tracing context managers. Instead, the design dictates passing a `RunnableConfig` mapped with an explicit `run_name`, tags, and metadata directly to `ainvoke()` or `invoke()` when the LangGraph state machine is triggered. LiteLLM callbacks (`litellm.success_callback = ['langsmith']`) must be explicitly attached.

## Implementation Approach
The implementation approach involves configuring `src/graph.py` to accept and pass `RunnableConfig`. Modify `src/services/workflow.py` to instantiate the `RunnableConfig` with project metadata and the `LANGCHAIN_PROJECT` variable before calling `graph.invoke()`. Attach `litellm.success_callback` globally at the entry point (`src/cli.py`).

## Test Strategy

### Unit Testing Approach
The unit tests will use `unittest.mock.patch` to verify that `RunnableConfig` is properly constructed and passed into the graph's invoke method without throwing type errors, and that `litellm.success_callback` is correctly appended.

### Integration Testing Approach
The integration testing approach will execute a full simulated cycle (from coding to failed UAT to auditor). Using `vcrpy` or specific mock patches, we will intercept the LangSmith API calls to verify that the State dictionary diffs and the Base64 image payloads are successfully formulated in the trace payload.
# CYCLE08 SPECIFICATION

## Summary
This final cycle implements Phase 3: The Observability Layer (LangSmith Integration). We will ensure the entire LangGraph orchestration layer is directly integrated with LangSmith. This provides total observability of the pipeline, visualizing complex routing and infinite loops, tracking state snapshot mutations between every node execution, and logging raw Vision LLM prompts natively.

## System Architecture
The architecture introduces native integration with LangSmith. Because LangChain and LangGraph natively support LangSmith via standard environment variables (`LANGCHAIN_TRACING_V2=true`), the architectural overhead is near-zero in implementation but profound in effect. The system architecture mandates that the LangGraph builder (e.g., `src/graph.py` or `src/services/workflow.py`) and all standalone LiteLLM calls must be executed within a traced context.

```text
/
├── src/
│   ├── **graph.py**
│   ├── **cli.py**
│   └── services/
│       └── **workflow.py**
```

## Design Architecture
The design architecture requires explicitly avoiding redundant tracing context managers. Instead, the design dictates passing a `RunnableConfig` mapped with an explicit `run_name`, tags, and metadata directly to `ainvoke()` or `invoke()` when the LangGraph state machine is triggered. LiteLLM callbacks (`litellm.success_callback = ['langsmith']`) must be explicitly attached.

## Implementation Approach
The implementation approach involves configuring `src/graph.py` to accept and pass `RunnableConfig`. Modify `src/services/workflow.py` to instantiate the `RunnableConfig` with project metadata and the `LANGCHAIN_PROJECT` variable before calling `graph.invoke()`. Attach `litellm.success_callback` globally at the entry point (`src/cli.py`).

## Test Strategy

### Unit Testing Approach
The unit tests will use `unittest.mock.patch` to verify that `RunnableConfig` is properly constructed and passed into the graph's invoke method without throwing type errors, and that `litellm.success_callback` is correctly appended.

### Integration Testing Approach
The integration testing approach will execute a full simulated cycle (from coding to failed UAT to auditor). Using `vcrpy` or specific mock patches, we will intercept the LangSmith API calls to verify that the State dictionary diffs and the Base64 image payloads are successfully formulated in the trace payload.
# CYCLE08 SPECIFICATION

## Summary
This final cycle implements Phase 3: The Observability Layer (LangSmith Integration). We will ensure the entire LangGraph orchestration layer is directly integrated with LangSmith. This provides total observability of the pipeline, visualizing complex routing and infinite loops, tracking state snapshot mutations between every node execution, and logging raw Vision LLM prompts natively.

## System Architecture
The architecture introduces native integration with LangSmith. Because LangChain and LangGraph natively support LangSmith via standard environment variables (`LANGCHAIN_TRACING_V2=true`), the architectural overhead is near-zero in implementation but profound in effect. The system architecture mandates that the LangGraph builder (e.g., `src/graph.py` or `src/services/workflow.py`) and all standalone LiteLLM calls must be executed within a traced context.

```text
/
├── src/
│   ├── **graph.py**
│   ├── **cli.py**
│   └── services/
│       └── **workflow.py**
```

## Design Architecture
The design architecture requires explicitly avoiding redundant tracing context managers. Instead, the design dictates passing a `RunnableConfig` mapped with an explicit `run_name`, tags, and metadata directly to `ainvoke()` or `invoke()` when the LangGraph state machine is triggered. LiteLLM callbacks (`litellm.success_callback = ['langsmith']`) must be explicitly attached.

## Implementation Approach
The implementation approach involves configuring `src/graph.py` to accept and pass `RunnableConfig`. Modify `src/services/workflow.py` to instantiate the `RunnableConfig` with project metadata and the `LANGCHAIN_PROJECT` variable before calling `graph.invoke()`. Attach `litellm.success_callback` globally at the entry point (`src/cli.py`).

## Test Strategy

### Unit Testing Approach
The unit tests will use `unittest.mock.patch` to verify that `RunnableConfig` is properly constructed and passed into the graph's invoke method without throwing type errors, and that `litellm.success_callback` is correctly appended.

### Integration Testing Approach
The integration testing approach will execute a full simulated cycle (from coding to failed UAT to auditor). Using `vcrpy` or specific mock patches, we will intercept the LangSmith API calls to verify that the State dictionary diffs and the Base64 image payloads are successfully formulated in the trace payload.
