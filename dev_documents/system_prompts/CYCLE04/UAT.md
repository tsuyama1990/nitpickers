# CYCLE04 UAT

## Test Scenarios

### Scenario ID: SCENARIO-04-1
**Priority**: High
This scenario tests the Pytest hook's capability to natively discover and parse execution blocks embedded in Markdown documentation. The user will place a mock `ALL_SPEC.md` containing two `python uat-scenario` blocks into the testing environment. They will invoke `uv run pytest` and verify that the runner discovers these blocks without requiring manual translation into `.py` files, eliminating the translation gap.

### Scenario ID: SCENARIO-04-2
**Priority**: High
This scenario verifies that the extracted `uat-scenario` blocks correctly execute and report failures dynamically. The user will write a deliberate failing assertion within a Markdown code fence. They will observe that when the test suite runs, Pytest accurately captures the execution failure and maps the traceback precisely to the block within the `.md` file, demonstrating robust reporting capabilities.

### Scenario ID: SCENARIO-04-3
**Priority**: Medium
This scenario tests isolation within the `exec()` context. Two markdown blocks will be executed: the first defines a local variable, and the second attempts to reference it. The user will verify that the second block throws a `NameError`, confirming that the Pytest runner properly isolates the execution scope of each scenario to prevent state pollution across documentation tests.

## Behavior Definitions

GIVEN a valid `.md` file containing properly formatted `python uat-scenario` blocks
WHEN the Pytest suite is invoked (`pytest tests/`)
THEN the custom hook identifies the file and extracts the blocks
AND Pytest successfully reports the execution results of the blocks natively in the console output.

GIVEN an intentionally failing Python assertion embedded in a Markdown file
WHEN the Pytest suite executes the `MarkdownItem`
THEN the dynamic evaluation of the string throws an AssertionError
AND Pytest captures the failure and associates it with the specific `scenario_N` item.

GIVEN two separate Python blocks within the same Markdown file
WHEN the `MarkdownItem.runtest` method executes them sequentially
THEN the execution namespace is strictly isolated
AND variables defined in the first block are utterly inaccessible in the second block.
