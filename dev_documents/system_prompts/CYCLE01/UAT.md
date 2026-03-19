# CYCLE01 UAT

## Test Scenarios

### Scenario ID: SCENARIO-01-1
**Priority**: High
This scenario tests the validation robustness of the Fix Plan schema. The core objective is to ensure that when the Stateless Auditor (the Vision LLM) generates a recovery plan, any deviation from the expected JSON structure is immediately caught by the Pydantic mechanical gatekeeper. The user will simulate an invalid API response lacking required fields and verify that the system refuses to process it, preventing hallucinated code from reaching the Stateful Worker.

### Scenario ID: SCENARIO-01-2
**Priority**: High
This scenario verifies the correct instantiation and serialization of the UAT Artifact models. When a dynamic Playwright test fails in the Outer Loop, it generates paths to screenshots and DOM traces. The user will simulate this failure by passing a dictionary of mock file paths into the UATResult schema. The test will confirm that the paths are parsed correctly, stored as strings, and that the model can be successfully serialized back to JSON for transmission to the observability layer.

### Scenario ID: SCENARIO-01-3
**Priority**: Medium
This scenario tests the backward compatibility of the core project state. By extending `state.py` to include UAT-specific fields, we must ensure existing workflows are not broken. The user will initialize the primary state object without providing any UAT or Fix Plan data, verifying that the new fields gracefully default to `None` and do not throw unexpected initialization errors during standard agent execution.

## Behavior Definitions

GIVEN the new `FixPlan` domain model is defined in the system
WHEN a dictionary representing a malformed JSON response (e.g., missing the `filepath` in a modification block) is passed to the constructor
THEN the system must immediately raise a Pydantic `ValidationError`
AND the error message must explicitly indicate the missing required fields.

GIVEN a valid dictionary containing standard error text, an exit code of 1, and valid mock paths to a `.png` and `.txt` file
WHEN this dictionary is parsed by the `UATResult` Pydantic model
THEN the model successfully instantiates without errors
AND the artifact paths are correctly resolved and accessible as attributes on the object.

GIVEN the core LangGraph state dictionary has been updated to include UAT fields
WHEN a legacy workflow initializes the state without providing `uat_result` or `current_fix_plan`
THEN the state initializes successfully
AND the newly added fields resolve to `None` implicitly, preserving backward compatibility.
