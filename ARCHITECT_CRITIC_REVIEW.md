# Architect Critic Review

## Architectural Stress Test
During a rigorous stress test of the proposed 5-Phase Architecture, the following vulnerabilities and edge cases were identified:

1.  **State Contamination on Rejection (Coder Graph):** If the `final_critic_node` rejects the code after a successful pass through the refactoring node, the flow routes back to `coder_session`. However, the `is_refactoring` flag remains `True`. On the next successful sandbox evaluation, the system will incorrectly bypass the auditors and jump straight back to the `final_critic_node` with un-audited code.
    *Resolution:* The router `route_final_critic` or the `coder_session` itself must explicitly reset `is_refactoring = False` and `current_auditor_index = 1` upon rejection.
2.  **Infinite Integration Loops (Integration Graph):** In Phase 3, if `git_merge_node` detects conflicts, it routes to `master_integrator_node`. If the LLM generates an invalid resolution that still contains Git markers, `git_merge_node` will send it right back. There is no `integration_attempt_count` limit analogous to the `audit_attempt_count`.
    *Resolution:* `IntegrationState` must be updated to include an `integration_attempt_count`, and the routing logic must forcefully abort or escalate after a defined threshold to prevent infinite loops.
3.  **Global Sandbox Failure Handling:** If the `global_sandbox_node` in Phase 3 fails, the flow routes back to the Integrator. This could also become an infinite loop if the error is systemic.
    *Resolution:* Limit the retries for global sandbox fixes.

## Alternative Approaches Considered

1.  **Nested Sub-Graphs vs. Sequential Orchestration:** We considered using LangGraph's nested sub-graph feature to embed Phase 2, 3, and 4 into a single monolithic graph.
    *Why current approach is superior:* A single massive graph makes state management incredibly complex, especially when Phase 2 requires `asyncio.gather` for parallel execution across entirely different PRs/branches. Keeping them decoupled and orchestrated via `WorkflowService` (CLI) allows for cleaner Pydantic state definitions (`CycleState` vs `IntegrationState`) and vastly simplifies testing and debugging.

2.  **Raw Conflict Markers vs. 3-Way Diff:** We evaluated simply passing the conflicted file (with `<<<<<<<` markers) to the LLM.
    *Why current approach is superior:* LLMs struggle significantly to parse overlapping logic intuitively. Extracting the Base, Local, and Remote versions provides the LLM with the chronological intent of the code, drastically increasing the success rate of complex logic merges.

## Conclusion
The high-level 5-Phase strategy is optimally designed for zero-trust validation. The architectural foundation is solid, but the Pydantic schemas and routing specifications in the original design lacked critical reset mechanisms for edge-case failure loops.

The documents `SYSTEM_ARCHITECTURE.md`, `CYCLE01/SPEC.md`, `CYCLE01/UAT.md`, `CYCLE02/SPEC.md`, and `CYCLE02/UAT.md` have been refined to enforce these strict loop limits and state resets, ensuring the pipeline remains deterministic and infinitely resilient.
