# User Test Scenario & Tutorial Plan: NITPICKERS (NEXUS-CDD)

## Aha! Moment
The "Magic Moment" occurs when the user initiates the system with a set of raw requirements, watches the `gen-cycles` command autonomously structure a highly complex, multi-cycle architecture perfectly avoiding standard anti-patterns, and then seamlessly dispatches parallel tasks. The true realization of value happens when the user witnesses the system catch its own hallucinated code via the isolated E2B sandbox, explicitly extracting the failure traceback, and fixing it autonomously without a single human keystroke. It is the realization that they are managing a virtual, self-correcting engineering team, rather than a single coding assistant.

## Prerequisites
Before engaging with the NITPICKERS framework, the user must ensure the following are available:
*   **API Keys**: Valid keys configured in `.env` for `JULES_API_KEY` (or equivalent primary reasoning model), `OPENROUTER_API_KEY` (for fast auditor/critic models), and `E2B_API_KEY` (critical for the sandbox execution environment).
*   **Docker Desktop/Engine**: Required to run the isolated AC-CDD container.
*   **uv**: The fast Python package installer and resolver.
*   **Python 3.12+**: If running specific components natively (though containerization is preferred).
*   **marimo**: To execute the interactive tutorial.

## Tutorial Strategy
The goal of the tutorial is to guide a new user through the complete capabilities of the NITPICKERS architecture, starting from a basic configuration and escalating to complex, parallel failure-recovery scenarios.

1.  **"Mock Mode" (CI/Verification)**: We will provide a robust mock configuration option within the tutorial. This mode simulates the API calls to Jules and OpenRouter using deterministic local responses, and simulates the E2B sandbox using safe, isolated local subprocesses. This ensures the tutorial can be run reliably in CI environments or by users without active API subscriptions to verify the state machine logic.
2.  **"Real Mode"**: This mode utilizes live API keys, demonstrating the true reasoning power of the AI and the actual physical isolation of the remote E2B sandbox.

The tutorial will progressively unveil features: First, the basic `gen-cycles` and Self-Critic validation. Second, the concurrent dispatcher unleashing Massive Throughput. Third, the Zero-Trust execution gate catching a deliberate error. Finally, the Semantic Merge conflict resolution.

## Tutorial Plan
The entire interactive learning experience will be contained within a single, beautifully structured Marimo notebook to ensure maximum reproducibility and ease of use.

*   **Filename**: `tutorials/nitpickers_comprehensive_tutorial.py`

This single file will encapsulate all scenarios:
1.  **Quick Start**: Initializing the project, parsing a simple requirement, and executing a single flawless cycle.
2.  **Advanced - The Red Team**: Deliberately providing a flawed initial blueprint and watching the Self-Critic node force a revision.
3.  **Advanced - Concurrent Execution**: Dispatching three cycles simultaneously and observing the reduced completion time via visual progress bars.
4.  **Advanced - The Zero-Trust Gate**: Injecting a failing test into the pipeline and watching the system extract the E2B traceback to autonomously correct the code.
5.  **Advanced - Semantic Merge**: Simulating a Git conflict between two concurrent branches and observing the Master Integrator node resolve it intelligently.

## Tutorial Validation
The generation of `tutorials/nitpickers_comprehensive_tutorial.py` will be the final automated task of Cycle 08. The system validation requires executing this Marimo file headlessly (`marimo run tutorials/nitpickers_comprehensive_tutorial.py`) within the final integration test suite. If the file executes from start to finish without raising an exception, it proves that not only does the software function, but the user experience is also strictly verified.

## Success Criteria
The ultimate success criteria for the user experience is that a developer can clone the repository, run `uv run marimo edit tutorials/nitpickers_comprehensive_tutorial.py`, execute the cells sequentially, and observe the entire autonomous development lifecycle—from planning to parallel execution to self-correction and final PR generation—execute flawlessly without errors in under 15 minutes.
