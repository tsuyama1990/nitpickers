# System Architecture

## Summary
The NITPICKERS system represents an advanced, AI-native software development environment specifically constructed to execute rigorous, zero-trust validation of automatically generated program code. This architectural blueprint introduces a comprehensive refactoring of the existing LangGraph-based intelligent agent workflow, transitioning it into a highly deterministic, fully decoupled, and extraordinarily robust "5-phase" configuration pipeline. The fundamental intent of this strategic transformation is to substantially reinforce the separation of algorithmic duties, absolutely guarantee programmatic state consistency, and establish an uncompromising, systematic methodology for autonomous code synthesis, red team diagnostic auditing, dynamic operational execution within a securely isolated and hermetically sealed sandbox, and seamless, automated source code conflict resolution. This system mandates absolute certainty, ensuring that no unverified code enters the integration phase.

This sophisticated structural overhaul deliberately leverages and enhances the pre-existing system foundations rather than discarding them. By selectively modifying explicit Pydantic-based domain state models, sophisticated graph routing logic, and precisely targeted service-layer use-cases, the architecture preserves backwards compatibility while achieving next-generation capabilities. The newly minted 5-phase structure will explicitly chart the precise chronological lifecycle of every discrete development cycle. This encompasses everything from the foundational requirement decomposition and planning phase, traversing through the rigorous implementation and testing phase, and culminating in the final continuous integration and comprehensive end-to-end user acceptance testing phase. Consequently, this intricate orchestration mathematically guarantees that absolutely every single line of synthesized logic strictly complies with rigorous structural linting rules and profoundly exhaustive behavioral testing checks before it can ever be flagged as formally accepted and fully verified.

## System Design Objectives
The predominant and overriding objective guiding this profound architectural refactoring is to systematically transition the current, potentially monolithic or overly tightly coupled LangGraph execution choreography into a rigorously defined, modular, and flawlessly executing 5-phase pipeline. This systemic evolution is engineered to address several paramount structural objectives that are absolutely critical for sustaining a highly scalable, dependable, and operationally resilient AI-driven software development environment.

Firstly, the architecture must emphatically enforce **Strict Role Separation** and rigid operational boundaries. By meticulously delineating the precise interaction boundaries dividing disparate specialized agents—specifically the visionary Architect, the pragmatic Coder, the critical Auditor, and the harmonizing Master Integrator—the system structurally precludes dangerous context bleeding. This profound separation deliberately reduces the cognitive processing load imposed on any individual language model. Such deliberate fragmentation ensures that every agent operates strictly within a surgically focused contextual scope, thereby exponentially elevating the qualitative output and technical precision of their respective contributions. For example, the Coder agent is restricted solely to algorithmic implementation and unit testing, whereas the inherently stateless Auditor agent operates exclusively as an impartial, independent diagnostician. The Auditor evaluates the Coder's synthesized output devoid of any historical bias or developmental fatigue, guaranteeing an objective and rigorous qualitative assessment.

Secondly, the architecture is absolutely mandated to ensure **Robust State Management**. The core LangGraph state, fundamentally orchestrated via the rigidly typed `CycleState` Pydantic model, requires significant augmentation to seamlessly govern exceptionally complex control flows. These flows encompass serialized, sequential auditing procedures and explicitly defined, iterative refactoring loops. Achieving this necessitates the strategic introduction of critical new state variables, particularly `is_refactoring`, `current_auditor_index`, and `audit_attempt_count`. The inclusion of these vital tracking metrics is utterly indispensable for monitoring the exact evolutionary progress of a cycle, meticulously enforcing retry limitations to structurally prohibit infinite recursive execution loops, and explicitly demarcating the critical transition separating the preliminary functional implementation phase from subsequent, dedicated code optimization and refactoring phases.

Thirdly, the engineered system emphatically prioritizes **Safe and Automated Integration**. A particularly significant and transformative enhancement is the formal introduction of a dedicated Integration Phase (Phase 3). This specific operational phase proactively confronts and systematically resolves the notorious complexities associated with merging parallel, concurrent code modifications. It achieves this by deploying an advanced, highly intelligent 3-Way Diff conflict resolution strategy. Rather than leaning on conventional, often fragile source control merge operations that frequently fail and demand manual, human intervention, the dedicated Master Integrator agent will cognitively synthesize any conflicting alterations. It accomplishes this by comprehensively analyzing the shared common ancestor (Base), the localized branch modifications (Local), and the concurrently conflicting remote modifications (Remote). This profound analysis ensures that the underlying architectural intentions driving both competing branches are harmoniously preserved and technically reconciled.

Fourthly, the fundamental architecture legally mandates absolute **Zero-Trust Validation**. Every single fragment of source code synthesized by the system must successfully navigate an uncompromising mechanical blockade. This dictates that any pull request, merge operation, or code integration attempt is explicitly and automatically blocked until absolutely all static analysis checks (including stringent Ruff linting and strict Mypy type validation) and all dynamic operational tests (such as exhaustive Pytest executions) report a completely successful, zero exit code. This foundational, non-negotiable principle completely eradicates the dangerous concept of assumed or partial success, mathematically guaranteeing that exclusively structurally sound, functionally correct, and rigorously verified code is permitted to progress through the automated pipeline.

Finally, the overarching design philosophy must remain unequivocally **Additive and Extensible**. The formulated refactoring strategy explicitly outlaws the perilous approach of rewriting the entire system architecture from absolute scratch. Instead, it intelligently leverages the robust, existing Pydantic schemas, dependency injection service containers, and comprehensive test testing frameworks. The architecture safely and meticulously extends these proven components to natively accommodate the complex new 5-phase execution logic. This conservative yet powerful additive approach purposefully minimizes operational disruption, strictly preserves all existing functional capabilities, and categorically ensures that the unified system can be effortlessly and securely adapted to satisfy any future, unforeseen operational requirements or to integrate newly developed, advanced agent capabilities as they emerge.

## System Architecture
The comprehensively refactored NITPICKERS system architecture is meticulously compartmentalized into five utterly distinct, strictly sequential operational phases. Each specific phase is exclusively governed by specialized LangGraph procedural nodes and securely interconnected through rigorously validated, highly defined conditional routing functions. This sophisticated, deeply modular methodology unequivocally guarantees that the entire software development sequence remains impeccably logical, inherently traceable, and overwhelmingly resilient against unexpected anomalies or procedural execution errors.

**Phase 0: Init Phase (CLI Setup)**
This preliminary phase is fundamentally responsible for the static, foundational initialization of the development environment. Triggered explicitly by manual CLI commands, it dynamically generates essential boilerplate configurations, flawlessly configures strict linting parameters within the central `pyproject.toml`, and officially establishes the structural bedrock of the operational workspace. It intrinsically relies on user-supplied parameters, notably the comprehensive `ALL_SPEC.md` document, to firmly anchor the programmatic requirements dictating the trajectory of all subsequent phases.

**Phase 1: Architect Graph (Requirement Planning)**
During this strategic phase, the visionary Architect agent comprehensively analyzes the raw, foundational requirements and systematically decomposes them into discrete, executable, and strictly sequential development cycles (e.g., `CYCLE01`). This sophisticated process intrinsically incorporates an automated red team self-critic review mechanism. This critical step mathematically guarantees that the formulated architectural plan is operationally viable, structurally sound, and meticulously organized before granting authorization to proceed. The definitive output characterizing this phase is an exhaustive set of precise specifications and corresponding User Acceptance Testing (UAT) documentation explicitly tailored for each mandated cycle.

**Phase 2: Coder Graph (Implementation and Audit)**
This phase represents the core, rigorous execution loop governing a specifically assigned cycle. The Coder agent autonomously implements the designated software features and their accompanying unit tests. Immediately following generation, the synthesized code is ruthlessly evaluated within a highly secure, locally isolated execution sandbox (subjecting it to unyielding static analysis and dynamic unit tests). Upon successfully passing this initial blockade, the code is forcibly subjected to a rigorous, serialized Audit process. This process involves a sequential review conducted by multiple, entirely independent Auditor agents. Should any single Auditor reject the code, it is immediately routed back to the Coder for mandatory revision. Once all Auditors unanimously approve the logic, the code advances to a dedicated, final Refactor node. This final step is designed to optimize code quality and structural elegance, subsequently demanding a final, flawless sandbox evaluation and a conclusive self-critic review.

**Phase 3: Integration Phase (3-Way Diff)**
Upon the absolutely successful culmination of all parallel Coder cycles, the system autonomously attempts to seamlessly merge the accumulated modifications into the primary integration branch. In the event that complex structural conflicts materialize, the Master Integrator agent immediately deploys an advanced 3-Way Diff analytical strategy. By comprehensively scrutinizing the Base ancestor code, the Branch A modifications, and the Branch B modifications, the agent intelligently synthesizes a harmonious resolution. The resultant integrated code is subsequently, mercilessly verified within a global, project-wide execution sandbox to unequivocally certify that the complex merge operation did not inadvertently introduce any hidden systemic regressions.

**Phase 4: UAT & QA Graph (Dynamic E2E Testing)**
The conclusive, final phase mandates exhaustive and uncompromising End-to-End (E2E) testing deployed against the newly integrated, complete codebase. Automated testing frameworks, such as Playwright, execute the intricate UAT scenarios established during Phase 1. If any test registers a failure, a dedicated, entirely stateless QA Auditor meticulously dissects the multi-modal failure artifacts (including execution logs and high-resolution DOM screenshots) and synthesizes a precise, actionable fix plan. This plan is transmitted to a specialized QA Session agent, which implements the necessary surgical corrections. This automated, self-healing loop operates continuously and tirelessly until absolutely all UAT scenarios pass flawlessly, officially signaling the absolute and triumphant completion of the comprehensive project cycle.

### Boundary Management and Separation of Concerns Rule
The system mandates explicit rules on boundary management. Cross-phase data leakage is strictly forbidden; states must be passed cleanly via Pydantic objects. The Coder must never evaluate its own final quality without the Auditor's approval. External APIs must be abstracted and explicitly mocked during sandbox evaluations to maintain perfect environmental resilience.

```mermaid
flowchart TD
    %% Phase0: Init Phase (CLI Setup)
    subgraph Phase0 ["Phase 0: Init Phase (CLI Setup)"]
        direction TB
        InitCmd([CLI: nitpick init])
        GenTemplates[".env.sample / .gitignore, strict ruff, mypy settings (Local)"]
        UpdateDocker["add .env path on docker-compose.yml (User)"]
        PrepareSpec["define ALL_SPEC.md (User)"]

        InitCmd --> GenTemplates --> UpdateDocker --> PrepareSpec
    end

    %% Phase1: Architect Graph
    subgraph Phase1 ["Phase 1: Architect Graph"]
        direction TB
        InitCmd2([CLI: nitpick gen-cycles])

        subgraph Architect_Phase ["JULES: Architect Phase"]
            ArchSession["architect_session\n(Requirement Decomposition)"]
            ArchCritic{"self-critic review\n(Plan Review)"}
        end

        OutputSpecs[/"Specs and UATs for each Cycle"/]

        PrepareSpec --> InitCmd2 --> ArchSession
        ArchSession --> ArchCritic
        ArchCritic -- "Reject" --> ArchSession
        ArchCritic -- "Approve" --> OutputSpecs
    end

    %% Phase2: Coder Graph
    subgraph Phase2 ["Phase 2: Coder Graph (Parallel: Cycle 1...N)"]
        direction TB
        CoderSession["JULES: coder_session\n(Implementation)"]
        SelfCritic["JULES: SelfCriticReview\n(Initial Review)"]
        SandboxEval{"LOCAL: sandbox_evaluate\n(Linter / Unit Test)"}

        AuditorNode{"OpenRouter: auditor_node\n(Serial: Auditor 1→2→3)"}
        RefactorNode["JULES: refactor_node\n(Refactoring)"]
        FinalCritic{"JULES: Final Self-critic\n(Final Review)"}

        OutputSpecs -->|Start Cycle N| CoderSession

        CoderSession -- "1st Time" --> SelfCritic --> SandboxEval
        CoderSession -- "2nd+ Time" --> SandboxEval

        SandboxEval -- "Fail" --> CoderSession
        SandboxEval -- "Pass (Implementing)" --> AuditorNode
        SandboxEval -- "Pass (Refactored)" --> FinalCritic

        AuditorNode -- "Reject" --> CoderSession
        AuditorNode -- "Pass All" --> RefactorNode

        RefactorNode --> SandboxEval

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
        QaAuditor["OpenRouter: qa_auditor\n(Diagnostic Analysis)"]
        QaSession["JULES: qa_session\n(Integration Fixes)"]
        EndNode(((END: Project Complete)))
    end

    %% Inter-Phase Connections
    FinalCritic -- "Approve (All PRs Ready)" --> MergeTry

    MergeTry -- "Conflict" --> MasterIntegrator
    MasterIntegrator --> MergeTry

    MergeTry -- "Success" --> GlobalSandbox
    GlobalSandbox -- "Fail" --> MasterIntegrator

    GlobalSandbox -- "Pass" --> UatEval

    UatEval -- "Fail" --> QaAuditor
    QaAuditor --> QaSession
    QaSession --> UatEval

    UatEval -- "Pass" --> EndNode
```

## Design Architecture
The design architecture intrinsically mandates absolute reliance on strictly typed Pydantic models to flawlessly enforce comprehensive data validation, structurally sound schema definitions, and impeccable data integrity throughout every facet of the operational pipeline. By strategically extending the pre-existing, mature models, the system brilliantly guarantees critical backward compatibility while seamlessly introducing the highly sophisticated, deterministic capabilities unequivocally required to power the complex, multi-tiered 5-phase execution structure. This guarantees precision and determinism at every juncture.

```text
src/
├── cli.py
├── state.py
├── graph.py
├── nodes/
│   └── routers.py
├── domain_models/
│   └── (Existing schemas...)
└── services/
    ├── conflict_manager.py
    ├── uat_usecase.py
    └── workflow.py
```

### Core Domain Pydantic Models Structure and Typing
The absolute, foundational centerpiece dictating state management across the entire architecture is the rigorously typed `CycleState` Pydantic model, permanently located within the heavily fortified `src/state.py` module. This highly critical model expertly aggregates a multitude of vital sub-states (such as the indispensable `CommitteeState`, `AuditState`, and `TestState`) to flawlessly and deterministically manage the intricate lifecycle of any given developmental cycle. To stringently enforce zero-trust policies, all pipeline nodes must inherit from a strongly typed Pydantic `BaseNode` configured with `ConfigDict(extra='forbid', strict=True, arbitrary_types_allowed=True, frozen=True)`.

To effectively support the complex new Phase 2 (Coder Graph) operational logic, the `CommitteeState` (which serves as the primary sub-model for orchestrating multi-agent collaboration) must be robustly extended to explicitly include these critical new fields:
- `is_refactoring: bool`: An unequivocally essential Boolean flag mathematically determining whether the active cycle has successfully navigated the grueling audit phase and is currently engaged in the dedicated, final refactoring loop.
- `current_auditor_index: int`: A strictly typed integer deterministically tracking exactly which specific auditor within the designated serial chain (e.g., sequentially from 1 to 3) is actively executing the current code review procedure.
- `audit_attempt_count: int`: A precisely calibrated integer counter explicitly monitoring the exact number of times an auditor has rejected the generated code. This counter functions as a vital, highly responsive circuit breaker, absolutely preventing catastrophic infinite execution loops.

For the execution of Phase 3 (Integration Graph), the highly specialized `IntegrationState` model is mandated to expertly govern all variables explicitly related to the complex merging process. This includes meticulously managing a deterministic queue of successfully validated feature branches (`branches_to_merge: list[str]`), rigorously tracking comprehensive lists of utterly unresolved merge conflicts, and constantly monitoring the precise, real-time status of the primary integration branch. This sophisticated state is strictly, exclusively aggregated by the central Orchestrator immediately following the successful completion of Phase 2.

### Clear Integration Points on Schema Objects Extension
The meticulously engineered, completely new schema objects brilliantly and seamlessly extend the highly robust, pre-existing domain objects. For instance, the highly critical routing functions—namely `route_sandbox_evaluate`, `route_auditor`, and `route_final_critic`—permanently located within `src/nodes/routers.py` will explicitly and relentlessly rely on the newly integrated, strictly typed fields embedded within the `CycleState` model. This allows them to flawlessly formulate complex, highly deterministic routing decisions (dynamically querying deeply embedded system configurations rather than foolishly relying on brittle, hardcoded operational limits).

Crucially, the complex operational transition bridging Phase 2 and Phase 3 formally mandates the execution of a highly robust **State Aggregator** mechanism operating deep within the central Orchestrator module (`workflow.py`). This sophisticated mechanism precisely extracts the fully validated `integration_branch` data from the deeply secure `SessionPersistenceState` of every single successful `CycleState`, subsequently utilizing this data to flawlessly populate the critical `IntegrationState.branches_to_merge` validation list. Furthermore, all LLM interactions—including critical Auditor feedback, complex Master Integrator conflict resolutions, and intricate Refactor modifications—must strictly, unyieldingly utilize Pydantic-based structured schema outputs (e.g., `ConflictResolutionSchema`) to absolutely guarantee flawless parsing execution and completely eliminate the significant inherent vulnerabilities inextricably linked to fragile, unpredictable markdown regex extraction techniques.

## Implementation Plan

### CYCLE01
- **Focus**: This single, unified cycle will comprehensively execute the absolute entirety of the monumental 5-phase architectural refactoring. This monumental undertaking encompasses meticulously modifying the deeply fundamental `CycleState` Pydantic models to flawlessly integrate robust serial auditing and dedicated refactoring control variables, masterfully rewiring the exceedingly complex LangGraph edges to accurately mirror the newly defined Phase 2 logic, engineering the sophisticated 3-Way Diff integration engine, and seamlessly orchestrating the final Phase 4 dynamic UAT process. This unified approach guarantees total system coherence.
- **Features Detail**:
  1. **Phase 1 & 2 Refactoring (State & Graph Engine)**: Fundamentally overhaul `src/state.py` to seamlessly embed the `is_refactoring`, `current_auditor_index`, and `audit_attempt_count` variables deeply within the `CommitteeState`. Develop and integrate the critical conditional routing functions (`route_sandbox_evaluate`, `route_auditor`, `route_final_critic`) inside `src/nodes/routers.py`. Comprehensively rewire `_create_coder_graph` inside `src/graph.py` to actively instantiate the new serial `auditor_node`, the dedicated `refactor_node`, and the conclusive `final_critic_node`.
  2. **Phase 3 Integration (3-Way Diff Engine)**: Formally engineer the exceedingly sophisticated 3-Way Diff intelligent conflict resolution matrix located within `src/services/conflict_manager.py`. This requires meticulously fetching the Base, Local, and Remote file states utilizing robust Git subprocess interactions, and structuring an impenetrable context prompt for the Master Integrator agent. Construct the `build_integration_graph` to successfully govern `git_merge_node` and `global_sandbox_node`.
  3. **Phase 4 Orchestration & QA (UAT Separation)**: Masterfully decouple `src/services/uat_usecase.py` to absolutely guarantee it only engages following the total completion of Phase 3. Refactor `src/services/workflow.py` to seamlessly execute the parallel invocation of Coder graphs, await their unanimous conclusion, definitively trigger the Integration phase, and conclude by initiating the QA Graph for comprehensive, end-to-end evaluation.

## Test Strategy

### CYCLE01
- **Unit Testing**:
  - **State Integrity**: Rigorously validate the structural modifications applied to `src/state.py` by extensively testing the modified Pydantic models. Methodically ensure that dynamically setting `is_refactoring` to True or intentionally incrementing `current_auditor_index` flawlessly triggers the appropriate Pydantic schema validation constraints, definitively proving that invalid internal states are systematically blocked.
  - **Routing Determinism**: Comprehensively test the highly intricate routing logic located within `src/nodes/routers.py` by systematically injecting meticulously mocked `CycleState` objects explicitly configured with wildly diverse permutations of boolean flags and execution counters. Assert with absolute precision that the functions return the exact, expected string trajectory (e.g., navigating to "auditor" versus routing to "final_critic").
  - **Diff Resolution Extraction**: Execute highly controlled, deeply isolated unit tests specifically targeting the `build_conflict_package` operational method within `src/services/conflict_manager.py`. Meticulously mock the underlying `ProcessRunner` Git calls to simulate highly complex file variations, subsequently verifying that the aggregated LLM prompt flawlessly integrates the distinct Base, Local, and Remote text block representations.
- **Integration Testing**:
  - **Graph Execution Paths**: Deploy comprehensive, multi-node integration tests to meticulously verify the beautifully rewired `_create_coder_graph` and the newly minted `build_integration_graph`. Flawlessly simulate a complete "Happy Path" demonstrating an uninterrupted flow traversing from the initial Coder session, seamlessly navigating the serial Auditor sequence, conquering the dedicated Refactor node, and finally emerging successfully at the terminal END node. Furthermore, meticulously simulate devastating "Rejection Loops" to definitively confirm that the system correctly increments the fail counters and reliably routes back to the Coder for immediate remediation.
- **E2E Strategy & Sandbox Resilience**:
  - **Mocking Protocol**: The overarching test strategy strictly mandates an unbreakable rule regarding external APIs. To guarantee absolute sandbox resilience and fundamentally prevent catastrophic infinite retry loops operating within isolated CI environments, **all external API calls relying on real secrets (e.g., OpenRouter, E2B, Jules) must be completely and unequivocally mocked** using advanced frameworks such as `respx` or Python's native `unittest.mock.AsyncMock`. The testing suite must successfully traverse the entire 5-phase execution flow utilizing these predetermined, static mock responses to definitively validate the underlying LangGraph structural state machine without actually executing costly live network transmissions.
  - **Database Rollback Rule**: Any integration testing requiring database interactions or persistent system state setup MUST utilize Pytest fixtures that automatically initiate a transactional session before the test executes, and strictly roll it back immediately afterward, ensuring lightning-fast state resets without relying on heavy external CLI cleanup commands.