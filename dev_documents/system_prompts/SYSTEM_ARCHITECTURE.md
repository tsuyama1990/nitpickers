# System Architecture

## Summary

This architectural document defines the structural modifications required to transition the Nitpickers AI-native development environment from its previous linear setup to a robust and scalable "5-Phase Architecture". This architecture introduces strict roles, well-defined phases, and a resilient red-teaming approach to ensure code quality through rigorous automated validations. The system relies heavily on a parallel implementation approach combined with a final multi-modal User Acceptance Testing (UAT) phase, leveraging the power of LangGraph for orchestration. The new architecture is designed to integrate seamlessly with the existing Pydantic-based state management, extending it carefully without destroying the current foundations.

## System Design Objectives

The core objective of this system redesign is to establish an unshakeable level of confidence in AI-generated code by enforcing absolute zero-trust validation through multiple, isolated layers of review and testing. We aim to construct an environment where pull requests are fundamentally blocked unless all static (linters, type checkers) and dynamic (sandbox execution) structural constraints are satisfied with a zero exit code. This mechanical blockade is essential to eliminate the common pitfall of assumed success in LLM-driven development.

Furthermore, the architecture must support concurrent execution. By transitioning to a "5-Phase Architecture", we decompose large feature requests into smaller, isolated, and parallel implementation cycles (Phase 2). This decomposition drastically reduces the cognitive load on the underlying LLMs and minimizes the blast radius of any generated errors. However, parallel execution introduces the challenge of integration, which is why Phase 3 (Integration Phase) is critical. It must employ an intelligent 3-Way Diff mechanism to safely resolve conflicts before exposing the merged code to global sandbox checks.

Resilience and self-healing are paramount. The system must utilize stateless auditing components—specifically Vision LLMs deployed via OpenRouter—to act as outer-loop diagnosticians (Phase 4). These auditors must analyze rich, multi-modal artifacts, such as Playwright UI screenshots and execution logs, without suffering from the context fatigue often experienced by the implementing agents. They are responsible for generating structured, actionable fix plans that the worker agents can execute.

Finally, the design must strictly adhere to the principles of separation of concerns and additive evolution. Existing domain models, particularly those based on Pydantic, must be extended safely. State variables necessary for controlling the new parallel loops and iteration limits (like `is_refactoring` and `current_auditor_index`) must be integrated without breaking backward compatibility. The entire pipeline must remain fully observable through LangSmith, ensuring every state mutation and API interaction is transparent.

## System Architecture

The Nitpickers platform orchestrates its zero-trust workflow across five distinct phases. This separation guarantees that planning, implementation, integration, and final validation operate in isolated contexts, reducing the risk of cascading failures.

### Boundary Management & Separation of Concerns

-   **State Encapsulation:** The LangGraph state (`CycleState`) must act as the sole source of truth during cycle execution. Nodes must not share data outside of this state object.
-   **Stateless Auditors:** The Auditor nodes (OpenRouter) must be completely stateless. They rely entirely on the provided diagnostic artifacts and the current codebase snapshot, ensuring they remain objective and free from implementation-phase context bias.
-   **Immutable Target Codebase:** The source code in the target workspace is mutated only by the explicit `GitManager` or File Operation tools. Direct file system access by generic nodes is prohibited to maintain traceability.

### 5-Phase Workflow Diagram

```mermaid
flowchart TD
    %% Phase0: Init Phase (CLI Setup)
    subgraph Phase0 ["Phase 0: Init Phase (CLI Setup)"]
        direction TB
        InitCmd([CLI: nitpick init])
    end

    %% Phase1: Architect Graph
    subgraph Phase1 ["Phase 1: Architect Graph"]
        direction TB
        InitCmd2([CLI: nitpick gen-cycles])
        ArchSession["JULES: architect_session\n(Requirement Decomposition)"]
        ArchCritic{"JULES: architect_critic\n(Red Team Self-Critic)"}
        InitCmd2 --> ArchSession
        ArchSession --> ArchCritic
        ArchCritic -- "Reject" --> ArchSession
    end

    %% Phase2: Coder Graph (Parallel: Cycle 1...N)
    subgraph Phase2 ["Phase 2: Coder Graph (Parallel: Cycle 1...N)"]
        direction TB
        CoderSession["JULES: coder_session\n(Test/Implementation)"]
        SelfCritic["JULES: self_critic\n(Pre-Sandbox Polish)"]
        SandboxEval{"LOCAL: sandbox_evaluate\n(Linter / Unit Test)"}
        AuditorNode{"OpenRouter: auditor_node\n(Serial: Auditor 1→2→3)"}
        RefactorNode["JULES: refactor_node\n(Post-Audit Refactor)"]
        FinalCritic["JULES: final_critic\n(Final Logic Verification)"]

        CoderSession --> SelfCritic
        SelfCritic --> SandboxEval
        SandboxEval -- "Pass" --> AuditorNode
        AuditorNode -- "Reject" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode
        RefactorNode --> SandboxEval
        SandboxEval -- "Pass (Post-Refactor)" --> FinalCritic
        FinalCritic -- "Reject" --> CoderSession
    end

    %% Phase3: Integration Phase
    subgraph Phase3 ["Phase 3: Integration Phase"]
        direction TB
        MergeTry{"Local: Git PR Merge\n(Integration Branch)"}
        MasterIntegrator["JULES: master_integrator\n(3-Way Diff Resolution)"]
        GlobalSandbox{"LOCAL: global_sandbox\n(Global Linter/Pytest)"}
    end

    %% Phase4: UAT & QA Graph
    subgraph Phase4 ["Phase 4: UAT & QA Graph"]
        direction TB
        UatEval{"LOCAL: uat_evaluate\n(Playwright E2E Tests)"}
        UxAuditor["OpenRouter: ux_auditor\n(Multimodal UX Review)"]
        QaAuditor["OpenRouter: qa_auditor\n(Diagnostic Analysis)"]
        QaSession["JULES: qa_session\n(Integration Fixes)"]
    end

    %% Inter-Phase Connections
    Phase0 --> Phase1
    Phase1 --> Phase2
    Phase2 -- "All Coder Cycles Complete" --> MergeTry

    MergeTry -- "Conflict" --> MasterIntegrator
    MasterIntegrator --> MergeTry
    MergeTry -- "Success" --> GlobalSandbox

    GlobalSandbox -- "Pass" --> UatEval

    UatEval -- "Fail" --> QaAuditor
    UatEval -- "Pass" --> UxAuditor
    QaAuditor --> QaSession
    QaSession --> UatEval
```

## Design Architecture

The structural foundation of Nitpickers relies heavily on Pydantic domain models to guarantee type safety and contract enforcement across all internal module interactions. The new features will be implemented by safely extending these existing schemas, ensuring seamless backward compatibility.

### Target File Structure

```text
src/
├── cli.py                     # Entrypoint updates for pipeline orchestration
├── config.py                  # Configuration updates
├── enums.py                   # State status enumerations
├── graph.py                   # Core 5-phase graph definitions
├── graph_nodes.py             # LangGraph node execution logic
├── state.py                   # Pydantic state definition (CycleState)
├── state_validators.py        # Pydantic field validators
├── nodes/
│   └── routers.py             # Conditional edge routing logic
└── services/
    ├── conflict_manager.py    # 3-Way Diff Git extraction and resolution
    ├── jules_client.py        # LLM interaction layers
    ├── uat_usecase.py         # Refactored standalone QA usage
    └── workflow.py            # Phase orchestration and concurrency
```

### Core Domain Pydantic Models Structure

The primary modification lies within `src/state.py`. We will extend the `CycleState` to support the new serial auditing and refactoring loops required by Phase 2. The core extension integrates a new sub-state, `CommitteeState`, which houses the control variables for the serial auditors. The integration points with existing domain objects remain non-destructive; legacy properties will be preserved via getters and setters mapped to the new nested structures.

```python
class CommitteeState(BaseModel):
    current_auditor_index: int = Field(default=1, ge=1)
    current_auditor_review_count: int = Field(default=1, ge=1)
    iteration_count: int = Field(default=0, ge=0)
    is_refactoring: bool = Field(default=False)
    audit_attempt_count: int = Field(default=0, ge=0)
    fallback_count: int = Field(default=0, ge=0)
    anti_patterns_memory: list[str] = Field(default_factory=list)
```

By encapsulating these properties into `CommitteeState` and composing it within `CycleState`, we ensure that the new workflow constraints do not pollute the root namespace, maintaining a clean and scalable state object.

## Implementation Plan

The project will be meticulously decomposed into two valid sequential implementation cycles.

### CYCLE01: The Coder Graph & State Foundation

The focus of the first cycle is establishing the robust looping mechanism for the core implementation phase (Phase 2). This requires updating the fundamental Pydantic state models to track the new routing metrics and completely rewiring the LangGraph definitions for the `coder_graph`.

**Features included:**
- Modification of `src/state.py` to include `is_refactoring`, `current_auditor_index`, and `audit_attempt_count`.
- Implementation of the required conditional routing logic in `src/nodes/routers.py` (`route_sandbox_evaluate`, `route_auditor`, `route_final_critic`).
- Complete rewiring of the `_create_coder_graph` method in `src/graph.py` to enforce the `coder_session` -> `self_critic` -> `sandbox_evaluate` -> `auditor_node` (serial loop) -> `refactor_node` -> `final_critic_node` execution flow.

### CYCLE02: Integration & QA Orchestration

The second cycle shifts focus to safely merging the parallel branches generated in Phase 2 and executing the final multi-modal UAT validations. This involves constructing the new `Integration Graph` and refining the standalone `QA Graph`.

**Features included:**
- Implementation of the `_create_integration_graph` in `src/graph.py` containing the `git_merge_node`, `master_integrator_node`, and `global_sandbox_node`.
- Development of the 3-Way Diff extraction logic within `src/services/conflict_manager.py`, utilizing Git commands to generate comprehensive context prompts for the Master Integrator LLM.
- Refactoring `src/services/uat_usecase.py` to operate exclusively within Phase 4, decoupled from Phase 2.
- Updates to `src/cli.py` and `src/services/workflow.py` to correctly orchestrate the sequential execution of Phase 1 through 4.

## Test Strategy

To guarantee the reliability of the new 5-Phase Architecture, a rigorous testing strategy must be applied across both cycles. We employ a strict Zero-Mock Policy for internal interactions, but mandate robust mocking for external API dependencies to ensure sandbox resilience.

### CYCLE01 Testing Approach

The primary risk in Cycle 01 is infinite looping within the LangGraph routing logic. We will employ unit tests specifically targeting the functions in `src/nodes/routers.py`. We will inject various combinations of `CycleState` values (e.g., `audit_attempt_count` exceeding thresholds, `is_refactoring` toggles) to assert that the router deterministically returns the correct subsequent node string. Additionally, we will write structural tests that instantiate the compiled `coder_graph` and trace the execution path using mock nodes that return predictable states.

### CYCLE02 Testing Approach

Testing the 3-Way Diff logic in Cycle 02 requires careful handling of Git states. We will utilize temporary directories (via Pytest fixtures) initialized as local bare repositories to simulate the target project. We will programmatically generate branches and conflict scenarios, then invoke the `conflict_manager` to verify it extracts the Base, Local, and Remote code strings accurately.

**DB Rollback Rule:** Any testing requiring database or persistent state setup MUST utilize Pytest fixtures that start a transaction before the test and roll it back after, ensuring lightning-fast state resets without relying on heavy external CLI cleanup commands.

Furthermore, all external API calls relying on secrets (e.g., simulated interactions with OpenRouter for the `master_integrator_node`) MUST be mocked in unit and integration tests using `pytest-mock`. The pipeline must not attempt real network calls during static verification, as the sandbox environment will not possess real API keys.
