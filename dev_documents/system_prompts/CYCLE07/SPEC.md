# CYCLE07 SPECIFICATION

## Summary
This cycle implements Phase 3: The Evaluation, Recovery, and Tracing Loop, focusing entirely on Self-Critic and Auditor Validation. To solve the "Hallucination Bottleneck" and "Context Dilution" inherent in long-running agent sessions, we introduce the Stateless Auditor powered by OpenRouter's Vision LLMs. We will pipe Outer Loop test failures—including textual error logs and Playwright multi-modal images captured in previous cycles—directly to this API. The system prompt will enforce an adversarial double-check sequence (the "Devil's Advocate" pattern) to prevent flaky false-positives and superficial fixes. Ultimately, this isolated node acts as a surgical "Sniper," diagnosing the true root cause of UI and HCD failures and outputting a highly structured, Pydantic-validated JSON 'Fix Plan' that the Stateful Worker can natively apply without losing its vast repository context.

## System Architecture
The architecture introduces the Stateless Auditor node (`src/nodes/auditor.py`) and its corresponding business logic in `src/services/auditor_usecase.py`. This component acts as the Outer Loop 'Sniper'. It is invoked purely on a per-request, stateless basis, meaning it brings absolutely zero context fatigue to the diagnosis.

Upon a UAT failure detected in CYCLE06, the LangGraph workflow conditional router directs the `UATResult` state (containing absolute paths to screenshots, DOM traces, and standard error) to this specialized auditor node. The architecture mandates that the auditor use case must securely read the `.png` file from disk, encode it into Base64 format, and package it alongside the DOM textual trace into a multimodal payload compatible with the LiteLLM library.

Crucially, the architecture enforces strict boundary management: the auditor must strictly return the `FixPlan` Pydantic model (defined in CYCLE01) serialized as JSON. It must never perform massive code rewrites or execute shell commands itself. The generated JSON Fix Plan is injected into the global state dictionary under `current_fix_plan`, and the workflow routes back to the Stateful Worker (`coder.py`). The Worker then blindly applies the surgical patch, treating the Auditor as an infallible diagnostic oracle. This decoupling prevents the Worker from getting stuck in infinite loops trying to guess why a UI test failed.

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
The design architecture requires configuring the OpenRouter integration natively via LiteLLM or direct HTTP asynchronous calls within the new `src/services/auditor_usecase.py`.

The system prompt template (`src/templates/AUDITOR_INSTRUCTION.md`) must be heavily modified. The design dictates the use of the "Devil's Advocate" self-critic loop: the prompt must explicitly instruct the LLM to analyze the screenshot, propose a fix, and then critically evaluate its own proposal for side-effects or regressions before finalizing the response.

Furthermore, the integration with LiteLLM must utilize strict structured outputs (e.g., OpenAI's `response_format={"type": "json_object"}` or equivalent tool-calling schemas) to force the Vision LLM to return data that perfectly matches the `FixPlan` Pydantic schema. The design relies on Pydantic's `model_validate_json()` to parse the LLM response. If the LLM hallucinates a malformed structure, Pydantic will throw a `ValidationError`, which the use case must catch, potentially triggering a localized retry mechanism without failing the entire graph execution.

## Implementation Approach
The implementation approach involves creating `src/services/auditor_usecase.py` and completely replacing the legacy, non-visual `qa_usecase.py`.

**Step 1:** Update `src/templates/AUDITOR_INSTRUCTION.md` to mandate structured JSON output and explicit adversarial reasoning steps.

**Step 2:** Within `AuditorUseCase`, implement an asynchronous method that extracts the `uat_result` from the state dictionary.

**Step 3:** Use Python's built-in file handling to safely read the `.png` from the path provided, encode it using `base64.b64encode`, and format it into a data URI (`data:image/png;base64,...`). Read the DOM `.txt` file similarly.

**Step 4:** Construct the multimodal LiteLLM payload, attaching the images, the DOM trace, and the system prompt. Call the LiteLLM asynchronous completion endpoint.

**Step 5:** Extract the raw JSON string from the LLM response. Use `FixPlan.model_validate_json(raw_string)` to parse it natively. If parsing fails, implement a short retry loop or return an explicit failure state.

**Step 6:** Assign the validated `FixPlan` to the `current_fix_plan` key in the state dictionary and return the mutated state to LangGraph.

## Test Strategy

### Unit Testing Approach
The unit tests will extensively use `unittest.mock.patch` on the LiteLLM `acompletion` function. We will simulate a successful Vision LLM response containing a valid JSON string that strictly conforms to the `FixPlan` schema. We will assert that the `AuditorUseCase` correctly reads the dummy file from disk, successfully applies Base64 encoding, formulates the correct LiteLLM payload structure, and flawlessly parses the returned JSON into the domain model. We will also write negative tests simulating malformed JSON from the LLM, verifying that the Pydantic `ValidationError` is caught and handled appropriately according to the retry logic.

### Integration Testing Approach
The integration testing approach will execute the auditor node transition within a mock LangGraph state machine. We will artificially inject a mock failing UAT state populated with a valid path to a dummy screenshot file. We will mock the network call to OpenRouter. We will verify that the node correctly executes the use case, that the returned mock `FixPlan` successfully updates the `current_fix_plan` attribute in the LangGraph state dictionary, and that the conditional router accurately directs the flow backward to the Worker node for implementation, validating the complete surgical recovery cycle.
