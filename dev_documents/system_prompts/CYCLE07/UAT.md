# CYCLE07 UAT

## Test Scenarios

### Scenario ID: SCENARIO-07-1
**Priority**: High
This scenario verifies the core functionality of the Stateless Auditor. The user triggers a UAT failure within the framework and verifies that the Stateless Auditor successfully intercepts the multi-modal artifacts (screenshot and DOM trace), analyzes them using the OpenRouter API, and generates a precise, schema-compliant JSON Fix Plan without encountering context window errors.

### Scenario ID: SCENARIO-07-2
**Priority**: High
This scenario tests the robustness of the schema validation. The user simulates an environment where the OpenRouter Vision LLM returns perfectly valid JSON that maps exactly to the `FixPlan` domain model. They verify that the `AuditorUseCase` parses this smoothly, updates the state dictionary, and routes the execution back to the inner loop seamlessly.

### Scenario ID: SCENARIO-07-3
**Priority**: Medium
This scenario tests the error handling capabilities of the auditor. The user uses a mocked LLM response to simulate the Vision LLM returning malformed JSON or conversational text instead of a strict object. They verify that the Pydantic `ValidationError` is correctly caught by the use case, preventing the malformed string from crashing the workflow and triggering an internal retry or graceful failure state.

## Behavior Definitions

GIVEN a completely failed Playwright test state containing a valid screenshot and DOM trace
WHEN the Stateless Auditor Node executes its validation sequence
THEN the OpenRouter API is successfully invoked with the Base64 encoded image and textual context
AND the node returns a properly validated Pydantic JSON Fix Plan detailing surgical file modifications.

GIVEN a valid JSON string returned from the Vision LLM that conforms to the schema
WHEN the `AuditorUseCase` processes the response
THEN the string is parsed natively into the `FixPlan` object
AND the `current_fix_plan` state attribute is correctly updated for the Stateful Worker to consume.

GIVEN a malformed, hallucinatory string returned from the Vision LLM
WHEN the `AuditorUseCase` attempts to parse it via Pydantic
THEN a `ValidationError` is mechanically raised and safely caught
AND the system attempts a retry or logs the parsing failure without corrupting the global application state.
