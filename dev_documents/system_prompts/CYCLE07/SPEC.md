# CYCLE07 SPECIFICATION

## Summary
This cycle implements Phase 3: The Evaluation, Recovery, and Tracing Loop focusing on Self-Critic and Auditor Validation. We will pipe Outer Loop test failures (logs + Playwright multi-modal images) directly to the OpenRouter API. The system prompt will enforce an adversarial double-check sequence (Devil's Advocate) to prevent flaky false-positives, ultimately outputting a highly structured JSON 'Fix Plan'.

## System Architecture
The architecture introduces the Stateless Auditor node (`src/nodes/auditor.py`) and corresponding use case. This acts as the Outer Loop 'Sniper'. It is invoked purely on a per-request, stateless basis, meaning it brings zero context fatigue to the problem. Upon UAT failure, the LangGraph workflow routes the `UATResult` state to this auditor node.

```text
/
├── src/
│   ├── nodes/
│   │   └── **auditor.py**
│   └── services/
│       └── **auditor_usecase.py**
├── src/templates/
│   ├── **AUDITOR_INSTRUCTION.md**
│   └── **QA_AUDITOR_INSTRUCTION.md**
```

## Design Architecture
The design architecture requires configuring the OpenRouter integration via LiteLLM or direct HTTP calls within the new `src/services/auditor_usecase.py`. The system prompt (`src/templates/AUDITOR_INSTRUCTION.md`) is heavily modified to enforce the Devil's Advocate self-critic loop.

## Implementation Approach
The implementation approach involves creating `src/services/auditor_usecase.py` replacing the legacy `qa_usecase.py`. Update instructions to mandate structured JSON output and adversarial reasoning. Within the use case, read the `.png` from the path provided in the state, Base64 encode it, and construct the multimodal LiteLLM payload. Parse the LLM response natively using Pydantic's `model_validate_json`.

## Test Strategy

### Unit Testing Approach
The unit tests will use `unittest.mock.patch` on the LiteLLM completion function. We will simulate a successful Vision LLM response containing a valid JSON string conforming to the `FixPlan` schema. We will assert that the `AuditorUseCase` correctly extracts, parses, and instantiates the domain model.

### Integration Testing Approach
The integration testing approach will execute the auditor node transition. We will inject a mock failing UAT state with a dummy screenshot file. We will verify that the OpenRouter API is called with the image encoded, and that the returned mock `FixPlan` successfully updates the LangGraph state dictionary before routing back to the Worker node.
# CYCLE07 SPECIFICATION

## Summary
This cycle implements Phase 3: The Evaluation, Recovery, and Tracing Loop focusing on Self-Critic and Auditor Validation. We will pipe Outer Loop test failures (logs + Playwright multi-modal images) directly to the OpenRouter API. The system prompt will enforce an adversarial double-check sequence (Devil's Advocate) to prevent flaky false-positives, ultimately outputting a highly structured JSON 'Fix Plan'.

## System Architecture
The architecture introduces the Stateless Auditor node (`src/nodes/auditor.py`) and corresponding use case. This acts as the Outer Loop 'Sniper'. It is invoked purely on a per-request, stateless basis, meaning it brings zero context fatigue to the problem. Upon UAT failure, the LangGraph workflow routes the `UATResult` state to this auditor node.

```text
/
├── src/
│   ├── nodes/
│   │   └── **auditor.py**
│   └── services/
│       └── **auditor_usecase.py**
├── src/templates/
│   ├── **AUDITOR_INSTRUCTION.md**
│   └── **QA_AUDITOR_INSTRUCTION.md**
```

## Design Architecture
The design architecture requires configuring the OpenRouter integration via LiteLLM or direct HTTP calls within the new `src/services/auditor_usecase.py`. The system prompt (`src/templates/AUDITOR_INSTRUCTION.md`) is heavily modified to enforce the Devil's Advocate self-critic loop.

## Implementation Approach
The implementation approach involves creating `src/services/auditor_usecase.py` replacing the legacy `qa_usecase.py`. Update instructions to mandate structured JSON output and adversarial reasoning. Within the use case, read the `.png` from the path provided in the state, Base64 encode it, and construct the multimodal LiteLLM payload. Parse the LLM response natively using Pydantic's `model_validate_json`.

## Test Strategy

### Unit Testing Approach
The unit tests will use `unittest.mock.patch` on the LiteLLM completion function. We will simulate a successful Vision LLM response containing a valid JSON string conforming to the `FixPlan` schema. We will assert that the `AuditorUseCase` correctly extracts, parses, and instantiates the domain model.

### Integration Testing Approach
The integration testing approach will execute the auditor node transition. We will inject a mock failing UAT state with a dummy screenshot file. We will verify that the OpenRouter API is called with the image encoded, and that the returned mock `FixPlan` successfully updates the LangGraph state dictionary before routing back to the Worker node.
# CYCLE07 SPECIFICATION

## Summary
This cycle implements Phase 3: The Evaluation, Recovery, and Tracing Loop focusing on Self-Critic and Auditor Validation. We will pipe Outer Loop test failures (logs + Playwright multi-modal images) directly to the OpenRouter API. The system prompt will enforce an adversarial double-check sequence (Devil's Advocate) to prevent flaky false-positives, ultimately outputting a highly structured JSON 'Fix Plan'.

## System Architecture
The architecture introduces the Stateless Auditor node (`src/nodes/auditor.py`) and corresponding use case. This acts as the Outer Loop 'Sniper'. It is invoked purely on a per-request, stateless basis, meaning it brings zero context fatigue to the problem. Upon UAT failure, the LangGraph workflow routes the `UATResult` state to this auditor node.

```text
/
├── src/
│   ├── nodes/
│   │   └── **auditor.py**
│   └── services/
│       └── **auditor_usecase.py**
├── src/templates/
│   ├── **AUDITOR_INSTRUCTION.md**
│   └── **QA_AUDITOR_INSTRUCTION.md**
```

## Design Architecture
The design architecture requires configuring the OpenRouter integration via LiteLLM or direct HTTP calls within the new `src/services/auditor_usecase.py`. The system prompt (`src/templates/AUDITOR_INSTRUCTION.md`) is heavily modified to enforce the Devil's Advocate self-critic loop.

## Implementation Approach
The implementation approach involves creating `src/services/auditor_usecase.py` replacing the legacy `qa_usecase.py`. Update instructions to mandate structured JSON output and adversarial reasoning. Within the use case, read the `.png` from the path provided in the state, Base64 encode it, and construct the multimodal LiteLLM payload. Parse the LLM response natively using Pydantic's `model_validate_json`.

## Test Strategy

### Unit Testing Approach
The unit tests will use `unittest.mock.patch` on the LiteLLM completion function. We will simulate a successful Vision LLM response containing a valid JSON string conforming to the `FixPlan` schema. We will assert that the `AuditorUseCase` correctly extracts, parses, and instantiates the domain model.

### Integration Testing Approach
The integration testing approach will execute the auditor node transition. We will inject a mock failing UAT state with a dummy screenshot file. We will verify that the OpenRouter API is called with the image encoded, and that the returned mock `FixPlan` successfully updates the LangGraph state dictionary before routing back to the Worker node.
