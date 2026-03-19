# CYCLE04 SPECIFICATION

## Summary
This cycle implements the core testing orchestration strategy for Phase 1: The Inner Loop (Structural Integrity & TDD). Our focus is to execute a "Docs-as-Tests" philosophy seamlessly integrating the UAT requirements directly mapped inside `ALL_SPEC.md` and `USER_TEST_SCENARIO.md`. Currently, the AI worker often hallucinates implementations due to a 'Translation Gap' when converting Markdown instructions into executable Python test files. To resolve this, we will develop custom Pytest hooks inside `tests/conftest.py` that natively parse these documentation files, dynamically extract the `uat-scenario` Python blocks, and yield them as natively executable Pytest items. This ensures the literal documented specifications serve as the true behavioral validation layer, executing dynamically within the sandboxed environment.

## System Architecture
The architecture introduces an integrated markdown parser hook for Pytest. By modifying `tests/conftest.py`, Pytest is equipped to read, parse, and execute code blocks embedded directly within markdown documentation. This eliminates the indirection of having the Stateful Worker explicitly rewrite test scenarios from markdown into Python files. Pytest items are dynamically generated for each `uat-scenario` block.

If the block represents a Marimo script or standard Python assertions, the custom Pytest item is responsible for evaluating the code within a securely isolated local context. The architecture treats the text in `ALL_SPEC.md` and `USER_TEST_SCENARIO.md` as the absolute source of truth. The custom `pytest.Item` and `pytest.File` classes defined in `conftest.py` will encapsulate the extracted strings, securely executing them using Python's built-in `exec()` with restrictive `globals` and `locals` dictionaries, or alternatively orchestrating them using `subprocess` if complete isolation is deemed necessary to prevent test suite contamination.

```text
/
├── tests/
│   └── **conftest.py**
```

## Design Architecture
The design utilizes standard Pytest hook specifications, specifically overriding `pytest_collect_file` and implementing the `pytest.Item` protocol. The design strategy mandates treating Markdown files as first-class citizens in the test runner.

The custom `MarkdownFile` class inherits from `pytest.File`. Its `collect` method parses the underlying `.md` file, using regular expressions to identify specific code fences (e.g., ```python uat-scenario). Each block is extracted and instantiated as a custom `MarkdownItem`. The `MarkdownItem` overrides the `runtest` method.

The primary invariant is that the execution of these extracted strings must not pollute the global Pytest runner state. Thus, the implementation requires constructing a fresh execution namespace and managing potential side effects, likely by leveraging Python's built-in `exec()` within a confined scope or utilizing a temporary directory context manager if file I/O operations are detected in the scenario.

## Implementation Approach
The implementation focuses on modifying `tests/conftest.py` without breaking existing standard Python unit tests.

**Step 1:** Define the `MarkdownItem(pytest.Item)` class. Override the `runtest` method. Inside `runtest`, compile the extracted string and execute it using `exec(self.code_string, {'__builtins__': __builtins__}, {})`. Ensure any raised exceptions are captured and reported properly by Pytest.

**Step 2:** Define the `MarkdownFile(pytest.File)` class. Override `collect`. Read the file contents, search for blocks tagged with `python uat-scenario`, and `yield MarkdownItem.from_parent(self, name=f"scenario_{index}", code_string=block)`.

**Step 3:** Implement the `pytest_collect_file` hook. Check if the `file_path.suffix == ".md"` and if the filename matches `ALL_SPEC.md` or `USER_TEST_SCENARIO.md`. If true, return the instantiated `MarkdownFile`. This simple yet powerful hook natively injects the documentation tests into the test suite.

## Test Strategy

### Unit Testing Approach
The unit tests will verify the parser logic and the custom Item execution within a controlled context. We will use `pytest.MonkeyPatch` or a temporary file fixture to create mock markdown files containing various combinations of valid and invalid `python uat-scenario` blocks. We will instantiate the `MarkdownFile` manually and iterate over its `collect()` generator, asserting that the correct number of `MarkdownItem` instances are yielded and that the extracted `code_string` is byte-for-byte accurate. We will explicitly test edge cases, such as multiple blocks, malformed blocks, and empty blocks.

### Integration Testing Approach
The integration testing approach will execute the Pytest runner in a subprocess (`pytest.main()`) pointing to a temporary directory containing our custom `conftest.py` and a mock `USER_TEST_SCENARIO.md` file. We will design one markdown block to pass (e.g., `assert 1 == 1`) and one to fail (`assert 1 == 0`). We will verify that Pytest correctly discovers the file, executes the embedded assertions natively, and standardly reports 1 pass and 1 failure in the output summary. This proves the Docs-as-Tests orchestration works flawlessly.
