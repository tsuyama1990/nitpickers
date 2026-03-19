Request for Proposal (RFP): Automated AI-Driven UAT Pipeline for NITPICKERS

1. Project Overview and Problem Statement

The NITPICKERS (formerly ac-cdd) framework represents a significant leap forward in autonomous software engineering. By successfully utilizing highly capable AI agents (specifically Jules) to orchestrate, design, and generate full-stack software directly from declarative markdown specifications (ALL_SPEC.md, README.md, SYSTEM_ARCHITECTURE.md), the framework has achieved unprecedented development velocity.

The Problem: The Hallucination Bottleneck, "Assumed Success", and the Black Box
Despite this high-velocity generation, the current pipeline suffers from a critical, systemic blind spot in its Quality Assurance (QA) phase. Currently, the User Acceptance Testing (UAT) phase operates on an "assumed success" model (specifically via the hardcoded # Assume UAT passes for now within uat_usecase.py). Consequently, numerous errors can be raised in the UAT phase after taking over the systems to users. This degrades the user experience significantly, which is likely to cause customer churn.

Furthermore, the existing qa_usecase.py relies entirely on static LLM code reviews. While Large Language Models are exceptionally proficient at reviewing syntax, they are fundamentally incapable of deterministically verifying dynamic application states.

Compounding this issue is the "Black Box" nature of complex agentic workflows. When an agent gets stuck in a loop trying to fix a bug, the standard console logs provide insufficient visibility into why the routing decision was made, what exact image was sent to the Vision LLM, or how the internal state mutated between nodes.

Objective
The objective of this proposal is to implement a fully automated, dynamic, and highly observable UAT pipeline that serves as an impenetrable mechanical gatekeeper. This pipeline must deterministically verify both structural backend logic and frontend Human-Centered Design (HCD) compliance within a local sandboxed environment. Crucially, the entire execution flow must be traced and monitored to provide instantaneous debugging and prompt-evaluation capabilities.

2. Core Architectural Philosophy: Worker, Auditor, and Observer

To build a resilient automated UAT system without falling into infinite debugging loops or context window collapse, this architecture strictly divides responsibilities between three core conceptual pillars:

2.1 The Stateful Worker (Jules via Gemini Pro)

Role: The "Inner Loop" Builder, Test Fabricator, and Executor.

Characteristics: Maintains long-running, stateful conversational sessions. It holds the massive, cumulative context of the repository and specifications.

Session Management Strategy: Because Jules is highly susceptible to "Context Dilution" (the "Lost in the Middle" phenomenon), session routing must be explicitly orchestrated:

Same Session Re-use (Session A): Used for fast-fixes (e.g., applying a "Fix Plan" from the Auditor).

New Session Creation (Session B): Spawned when successfully advancing to a new Development Cycle to systematically flush accumulated chat history.

Responsibility: Fabricating feature code, generating Pytest scripts, and achieving a 100% pass rate on structural unit/integration tests before advancing to PR creation.

2.2 The Stateless Auditor (OpenRouter)

Role: The "Outer Loop" Diagnostician, Critic, and HCD Evaluator.

Characteristics: Invoked on a strict, per-request, stateless basis, bringing zero "context fatigue" to a problem.

Responsibility: The Auditor acts as the "Sniper." When a true E2E UAT fails in the sandbox, OpenRouter is fed only the specific error log, code snippet, and visual artifacts (screenshots). It diagnoses the true root cause and outputs a surgical, precise JSON "Fix Plan" rather than a massive code rewrite.

2.3 The Observability Layer (LangSmith Integration)

Role: The "Panopticon" for tracing, debugging, and continuous evaluation.

Characteristics: Integrated directly into the LangGraph orchestration layer with near-zero implementation cost.

Responsibility & Benefits:

Visualizing Complex Routing & Infinite Loops: LangGraph's weakness is tracing complex node transitions (e.g., coder ➔ sandbox_evaluator ➔ coder_critic). LangSmith visually traces these edges, instantly exposing exactly where the system is stuck in an infinite loop.

State Snapshot Tracking (Diffs): Records the exact mutation of the State dictionary (e.g., uat_exit_code, current_fix_plan) between every node execution, eliminating the need for excessive print debugging.

Vision LLM Prompt/Response Verification: Completely logs the raw prompt (including the encoded screenshot image) sent to the uat_auditor and its exact response (latency, token usage). This instantly clarifies if an HCD failure was due to the LLM's reasoning or a blank screenshot being sent.

Evaluation and Prompt Engineering: Transforms failed UAT traces into datasets. When system prompts (like UAT_AUDITOR_INSTRUCTION.md) are updated, these datasets can be used for quantitative regression testing to verify that prompt adjustments actually improve repair accuracy.

3. Implementation Requirements

Phase 0: The Environment & Observability Setup Gate

Context: Real E2E tests require local secrets and hardware contexts. Furthermore, tracing must be active from the very first execution.

Requirements:

Interception Point: Modify the post-gen-cycles phase within cli.py or the ManagerUseCase.

Automated Dependency Scanning: Scan SPEC.md documents for required external dependencies (e.g., DATABASE_URL, OPENAI_API_KEY).

LangSmith Setup: The system MUST also explicitly require LangSmith environment variables to ensure total observability of the pipeline.

Hard Stop Prompt Example: "⚙️ Cycle planning complete. Please ensure required secrets (e.g., API keys) AND your LangSmith tracing variables (LANGCHAIN_TRACING_V2=true, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT='nitpickers-uat-pipeline') are correctly populated in your local '.env' file before proceeding with the run-cycle phase."

Phase 1: The Inner Loop (Structural Integrity & TDD)

Requirements:

Strategy 1 - Docs-as-Tests (Pytest Orchestration):

Implement a custom Pytest hook (pytest_collect_file in tests/conftest.py) to natively parse ALL_SPEC.md or README.md.

Dynamically extract uat-scenario markdown blocks and yield them as natively executable Pytest items to eliminate the LLM "Translation Gap".

Strategy 2 - Backend Verification & Gatekeeping (Mechanical Blockade):

Integrate ProcessRunner to execute generated unit tests locally.

Mechanically enforce strict Type Checking (uv run mypy .) and Linting (uv run ruff check .).

Block PR creation absolutely if a non-zero exit code is detected, automatically kicking the stderr trace back to Jules's active session.

Phase 2: The Outer Loop (Behavioral Reality Sandbox)

Requirements:

Strategy 3 - Playwright Multi-Modal Capture:

Integrate the pytest-playwright plugin into the test suite.

Automatically capture Multi-Modal Artifacts (full-page screenshots, DOM traces, console logs) upon any test failure or UI exception.

Dynamic Execution (uat_usecase.py):

Replace the # Assume UAT passes for now placeholder with an asynchronous ProcessRunner execution of the Pytest/Playwright suite.

Phase 3: The Evaluation, Recovery, and Tracing Loop

Requirements:

Strategy 4 - Self-Critic and Auditor Validation:

Pipe Outer Loop test failures (logs + Playwright images) to the OpenRouter API.

Enforce an adversarial double-check sequence (Devil's Advocate) in the system prompt to prevent flaky test false-positives.

Fix Plan Generation & Stateful Recovery:

The Auditor must output a highly structured, surgical JSON "Fix Plan".

Pipe this JSON directly back into Jules's existing active session (Session A) for immediate execution.

Strategy 5 - LangSmith Observability Integration:

Ensure the LangGraph builder (e.g., graph.py or workflow.py) is executed within an environment where LANGCHAIN_TRACING_V2=true is respected.

Verify that the custom State object (containing the current_fix_plan and uat_exit_code) is correctly serialized and visible in the LangSmith UI for every node transition.

4. Target Files for Modification

.env.example & Configuration: Add LANGCHAIN_TRACING_V2, LANGCHAIN_ENDPOINT, LANGCHAIN_API_KEY, and LANGCHAIN_PROJECT templates.

src/cli.py & src/services/workflow.py: Inject the Phase 0 Environment & Observability Gate logic. Manage Jules's Session lifecycles.

src/services/uat_usecase.py: Rewrite to instantiate a ProcessRunner that triggers Pytest dynamically, capturing exit codes to block merges.

src/services/qa_usecase.py (or new auditor_usecase.py): Interface with OpenRouter passing multi-modal artifacts, ensuring these calls are properly traced by LangSmith.

tests/conftest.py: Develop Pytest hooks for Docs-as-Tests and configure Playwright artifact capture.

src/templates/: Update Auditor instructions to mandate JSON "Fix Plans" and enforce the Devil's Advocate self-critic loop.

5. Acceptance Criteria

Environment & Tracing Gate: The CLI mechanically halts after gen-cycles, refusing to trigger the run-cycle loop until the user acknowledges both the .env operational requirements AND the LangSmith tracing variables.

Markdown Executability: Pytest successfully parses and executes a uat-scenario block directly from ALL_SPEC.md.

Mechanical Blockade: The orchestration layer refuses to raise a PR if ruff, mypy, or Playwright UATs fail, kicking the trace back to the same active Jules session.

Multi-Modal Capture: pytest-playwright automatically generates a screenshot and DOM trace on simulated UI failure.

Surgical Recovery: The OpenRouter Auditor generates a schema-compliant JSON "Fix Plan" from the artifacts, which Jules successfully applies.

Total Observability (LangSmith): A complete, end-to-end execution of a failing cycle must be visible in the LangSmith UI. The trace must definitively show:

The visual flowchart of node routing (proving/disproving infinite loops).

The State dictionary Diff between the uat node and the coder node.

The raw inputs (including the base64 encoded screenshot) and outputs (JSON Fix Plan) of the Vision LLM call.
