# CYCLE 05 Specification: Red Team Auditor & Intra-Cycle Refactor

## Summary
The objective of CYCLE 05 is to enforce a **Red Teaming Intra-Cycle** philosophy. After the Coder successfully passes the E2B sandbox dynamic tests, the code enters a strict audit phase. Rather than basic "code smell" checks, the Auditor acts as a malicious actor attempting to break the architecture. Fixed prompts (`CODER_CRITIC_INSTRUCTION.md`, `POST_AUDIT_REFACTOR_INSTRUCTION.md`) are created to ensure the Auditor strictly checks for N+1 issues, security flaws, race conditions, and adherence to DRY principles. Furthermore, a new `Self-Critic` node is added after the Auditor to perform a final self-reflection on refactoring opportunities before merging.

## System Architecture
This cycle builds on the existing `auditor_node` and introduces new nodes and rigid prompts.

### File Structure Blueprint
```text
/
├── pyproject.toml
├── src/
│   ├── graph.py                 (Update: Add post-audit Self-Critic refactoring node)
│   ├── graph_nodes.py           (Update: Implement Self-Critic logic for Coder graph)
│   └── services/
│       ├── auditor_usecase.py   (Update: Use fixed RED_TEAM prompts)
│       └── self_critic_evaluator.py (Reuse: From Architect phase, adapt for Coder phase)
└── dev_documents/
    └── system_prompts/
        ├── CODER_CRITIC_INSTRUCTION.md (New: Fixed RED_TEAM prompts)
        └── POST_AUDIT_REFACTOR_INSTRUCTION.md (New: Refactoring instructions)
```
**Modifications:**
- **`src/services/auditor_usecase.py`**: Inject `CODER_CRITIC_INSTRUCTION.md` instead of general review prompts.
- **`src/graph.py`**: Add `coder_critic_node` immediately following `committee_manager`.
- **`src/graph_nodes.py`**: Implement the routing logic for `coder_critic_node` (to `coder_session` if refactoring is needed, else to `uat_evaluate` or `END`).

## Design Architecture
### Pydantic Models & Extensibility
1. **`CriticResult` (Reused):**
   - We reuse the `CriticResult` from CYCLE 02. The difference is the prompt context. The Coder Critic receives the source code, AST, and test results, not just the architecture blueprints.
2. **Fixed Prompts:**
   - **`CODER_CRITIC_INSTRUCTION.md`:** "As a Red Team Auditor, your goal is to find critical flaws in the provided code. Check for: 1) Hardcoded secrets. 2) Race conditions. 3) N+1 database/API queries. 4) Unhandled exceptions."
   - **`POST_AUDIT_REFACTOR_INSTRUCTION.md`:** "The code is functionally correct but may be messy. Identify any duplicate logic or overly complex methods (McCabe > 10). Suggest a refactored version without breaking tests."

### Red Team Constraints
The Auditor is forbidden from writing code. It only outputs criticism and explicit file/line references. The Coder session must process this feedback, rewrite the code, and pass the E2B sandbox *again* before re-entering the Auditor loop. This ensures "Green" is maintained through refactoring.

## Implementation Approach
1. **Prompts Creation:** Write `CODER_CRITIC_INSTRUCTION.md` and `POST_AUDIT_REFACTOR_INSTRUCTION.md`. Ensure they output structured lists.
2. **Auditor Update:** In `src/services/auditor_usecase.py`, swap the basic instruction template for `CODER_CRITIC_INSTRUCTION.md`. It sends the diff to the OpenRouter/Jules LLM and parses the result.
3. **Graph Modification:** In `src/graph.py`, add `coder_critic` after the `committee_manager` (if `committee_manager` approves).
4. **Self-Critic Node:** In `src/graph_nodes.py`, the `coder_critic` uses the same Jules session as the Coder. It sends the `POST_AUDIT_REFACTOR_INSTRUCTION.md`. If the Jules session identifies improvements, it sets `status = CODER_RETRY` and loops back to `coder_session`. If it identifies none, it returns `COMPLETED` and ends the cycle.

## Test Strategy
### Unit Testing Approach
- Test the `auditor_usecase.py` by mocking the LLM to return a list of vulnerabilities (e.g., "N+1 query found in line 45"). Verify the usecase correctly maps this to `AuditResult.is_approved = False` and updates the state.
- Test the `coder_critic_node` by mocking a "No improvements needed" response and asserting it routes to `COMPLETED`. Mock an "Improvement suggested" response and assert it routes to `CODER_RETRY`.

### Integration Testing Approach
- In `test_workflow.py`, simulate a full Coder graph loop: `START` $\rightarrow$ `coder_session` $\rightarrow$ (mock E2B success) $\rightarrow$ `auditor` (mock Red Team failure) $\rightarrow$ `committee_manager` $\rightarrow$ `coder_session` $\rightarrow$ (mock E2B success) $\rightarrow$ `auditor` (mock success) $\rightarrow$ `committee_manager` $\rightarrow$ `coder_critic` (mock success) $\rightarrow$ `END`.
- Assert that the retry counters are correctly incremented and that max retries force an exit or a bypass based on configuration.