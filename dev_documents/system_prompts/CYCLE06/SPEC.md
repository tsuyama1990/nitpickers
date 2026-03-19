# CYCLE06 SPECIFICATION

## Summary
This cycle implements Phase 2: The Outer Loop (Behavioral Reality Sandbox) focusing on Dynamic Execution within `uat_usecase.py`. We will permanently replace the legacy '# Assume UAT passes for now' placeholder with an asynchronous `ProcessRunner` execution of the complete Pytest/Playwright suite, enforcing the dynamic gatekeeper. Rather than relying on static assertions, `src/services/uat_usecase.py` delegates execution to the `ProcessRunner` established in CYCLE03. It orchestrates the asynchronous execution of `uv run pytest tests/` with the playwright capture hooks active. The result of this execution maps directly to the `uat_models.py` schema. If the tests pass, the pipeline advances linearly. If they fail, the state dictionary is updated with the captured exit codes, error logs, and multi-modal artifact paths, routing the state vector directly to the Stateless Auditor node.

## System Architecture
The architecture introduces the dynamic outer loop execution model. The `src/services/uat_usecase.py` orchestrates the asynchronous execution. This service encapsulates the orchestration logic, translating raw command-line execution results into structured Pydantic state dictionaries required by the LangGraph state machine.

```text
/
├── src/
│   └── services/
│       └── **uat_usecase.py**
```

## Design Architecture
The design relies on robust execution logic within `uat_usecase.py`. The `UatUseCase` must parse the standard output and standard error from the `ProcessRunner` and dynamically locate the generated screenshot paths from the designated output directory (e.g., `dev_documents/test_artifacts/`). This maps the results into the `UATResult` Pydantic model.

## Implementation Approach
The implementation approach involves rewriting `src/services/uat_usecase.py`. Remove the hardcoded pass logic. Instantiate a `ProcessRunner` and `await` the execution of Pytest. Capture the combined standard output and error. If the return code is non-zero, traverse the `dev_documents/test_artifacts/` directory to locate newly created `.png` and `.txt` files. Instantiate the `UATResult` Pydantic model containing the exit code, logs, and paths. We must ensure this service is injected cleanly into the LangGraph state manager.

## Test Strategy

### Unit Testing Approach
The unit tests will use `unittest.mock.patch` to mock the `ProcessRunner` execution. We will simulate a successful run returning exit code 0 and a failed run returning exit code 1 with mock paths. We will verify that the `UatUseCase` correctly parses the exit code and instantiates the `UATResult` model accurately.

### Integration Testing Approach
The integration testing approach will invoke the `UatUseCase` in a mock application context containing a simple, pre-configured failing Pytest script. We will assert that the use case executes the script, captures the non-zero exit code, locates the generated screenshot, and correctly populates the state dictionary with the artifact path.
# CYCLE06 SPECIFICATION

## Summary
This cycle implements Phase 2: The Outer Loop (Behavioral Reality Sandbox) focusing on Dynamic Execution within `uat_usecase.py`. We will permanently replace the legacy '# Assume UAT passes for now' placeholder with an asynchronous `ProcessRunner` execution of the complete Pytest/Playwright suite, enforcing the dynamic gatekeeper. Rather than relying on static assertions, `src/services/uat_usecase.py` delegates execution to the `ProcessRunner` established in CYCLE03. It orchestrates the asynchronous execution of `uv run pytest tests/` with the playwright capture hooks active. The result of this execution maps directly to the `uat_models.py` schema. If the tests pass, the pipeline advances linearly. If they fail, the state dictionary is updated with the captured exit codes, error logs, and multi-modal artifact paths, routing the state vector directly to the Stateless Auditor node.

## System Architecture
The architecture introduces the dynamic outer loop execution model. The `src/services/uat_usecase.py` orchestrates the asynchronous execution. This service encapsulates the orchestration logic, translating raw command-line execution results into structured Pydantic state dictionaries required by the LangGraph state machine.

```text
/
├── src/
│   └── services/
│       └── **uat_usecase.py**
```

## Design Architecture
The design relies on robust execution logic within `uat_usecase.py`. The `UatUseCase` must parse the standard output and standard error from the `ProcessRunner` and dynamically locate the generated screenshot paths from the designated output directory (e.g., `dev_documents/test_artifacts/`). This maps the results into the `UATResult` Pydantic model.

## Implementation Approach
The implementation approach involves rewriting `src/services/uat_usecase.py`. Remove the hardcoded pass logic. Instantiate a `ProcessRunner` and `await` the execution of Pytest. Capture the combined standard output and error. If the return code is non-zero, traverse the `dev_documents/test_artifacts/` directory to locate newly created `.png` and `.txt` files. Instantiate the `UATResult` Pydantic model containing the exit code, logs, and paths. We must ensure this service is injected cleanly into the LangGraph state manager.

## Test Strategy

### Unit Testing Approach
The unit tests will use `unittest.mock.patch` to mock the `ProcessRunner` execution. We will simulate a successful run returning exit code 0 and a failed run returning exit code 1 with mock paths. We will verify that the `UatUseCase` correctly parses the exit code and instantiates the `UATResult` model accurately.

### Integration Testing Approach
The integration testing approach will invoke the `UatUseCase` in a mock application context containing a simple, pre-configured failing Pytest script. We will assert that the use case executes the script, captures the non-zero exit code, locates the generated screenshot, and correctly populates the state dictionary with the artifact path.
# CYCLE06 SPECIFICATION

## Summary
This cycle implements Phase 2: The Outer Loop (Behavioral Reality Sandbox) focusing on Dynamic Execution within `uat_usecase.py`. We will permanently replace the legacy '# Assume UAT passes for now' placeholder with an asynchronous `ProcessRunner` execution of the complete Pytest/Playwright suite, enforcing the dynamic gatekeeper. Rather than relying on static assertions, `src/services/uat_usecase.py` delegates execution to the `ProcessRunner` established in CYCLE03. It orchestrates the asynchronous execution of `uv run pytest tests/` with the playwright capture hooks active. The result of this execution maps directly to the `uat_models.py` schema. If the tests pass, the pipeline advances linearly. If they fail, the state dictionary is updated with the captured exit codes, error logs, and multi-modal artifact paths, routing the state vector directly to the Stateless Auditor node.

## System Architecture
The architecture introduces the dynamic outer loop execution model. The `src/services/uat_usecase.py` orchestrates the asynchronous execution. This service encapsulates the orchestration logic, translating raw command-line execution results into structured Pydantic state dictionaries required by the LangGraph state machine.

```text
/
├── src/
│   └── services/
│       └── **uat_usecase.py**
```

## Design Architecture
The design relies on robust execution logic within `uat_usecase.py`. The `UatUseCase` must parse the standard output and standard error from the `ProcessRunner` and dynamically locate the generated screenshot paths from the designated output directory (e.g., `dev_documents/test_artifacts/`). This maps the results into the `UATResult` Pydantic model.

## Implementation Approach
The implementation approach involves rewriting `src/services/uat_usecase.py`. Remove the hardcoded pass logic. Instantiate a `ProcessRunner` and `await` the execution of Pytest. Capture the combined standard output and error. If the return code is non-zero, traverse the `dev_documents/test_artifacts/` directory to locate newly created `.png` and `.txt` files. Instantiate the `UATResult` Pydantic model containing the exit code, logs, and paths. We must ensure this service is injected cleanly into the LangGraph state manager.

## Test Strategy

### Unit Testing Approach
The unit tests will use `unittest.mock.patch` to mock the `ProcessRunner` execution. We will simulate a successful run returning exit code 0 and a failed run returning exit code 1 with mock paths. We will verify that the `UatUseCase` correctly parses the exit code and instantiates the `UATResult` model accurately.

### Integration Testing Approach
The integration testing approach will invoke the `UatUseCase` in a mock application context containing a simple, pre-configured failing Pytest script. We will assert that the use case executes the script, captures the non-zero exit code, locates the generated screenshot, and correctly populates the state dictionary with the artifact path.
