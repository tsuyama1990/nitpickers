# CYCLE 02 Specification: Architect Self-Critic Node Integration

## Summary
The goal of CYCLE 02 is to introduce a **Self-Critic Evaluator** node into the Architect phase (`gen-cycles`). This node evaluates the generated `SYSTEM_ARCHITECTURE.md` and `CYCLE/SPEC.md` against fixed, rigorous anti-pattern prompts (e.g., checking for N+1 problems, race conditions, and lack of integration constraints). If vulnerabilities are detected, the node forces the Architect to regenerate the plans. This ensures that the generated blueprints are highly robust, providing "Interface Locks" that subsequent concurrent cycles can rely on without causing massive conflicts later.

## System Architecture
This cycle involves modifying `src/graph.py` and `src/graph_nodes.py` to add the Self-Critic node and creating fixed prompts for evaluation.

### File Structure Blueprint
```text
/
├── pyproject.toml
├── src/
│   ├── graph.py                 (Update: Add Self-Critic node to Architect graph)
│   ├── graph_nodes.py           (Update: Implement Architect Self-Critic logic)
│   └── services/
│       ├── architect_usecase.py (Update)
│       └── self_critic_evaluator.py (New: Evaluator logic)
└── dev_documents/
    └── system_prompts/
        └── ARCHITECT_CRITIC_INSTRUCTION.md (New: Fixed prompts for Architect Critic)
```
**Modifications:**
- **`src/graph.py`**: Add `architect_critic` node between `architect_session` and `END`.
- **`src/graph_nodes.py`**: Add `architect_critic_node` and routing logic `route_architect_critic`.
- **`src/services/self_critic_evaluator.py`**: Implement the LLM calls to Jules using the new fixed prompts to validate the generated specs.

## Design Architecture
### Pydantic Models & Extensibility
1. **`CriticResult`:**
   - Properties: `is_approved` (bool), `vulnerabilities` (list[str]), `suggestions` (list[str]).
   - Consumer: Architect UseCase (to apply feedback).
2. **`ARCHITECT_CRITIC_INSTRUCTION.md`:**
   - A markdown file containing a rigid verification checklist:
     - Check 1: N+1 DB Queries.
     - Check 2: Race conditions in concurrent data modification.
     - Check 3: Missing interface locks (missing API payload schema).
     - Check 4: Unhandled edge cases.
   - It forces the AI to output a structured JSON or parsable text matching the `CriticResult` schema.

### Interface Constraints
The Self-Critic logic utilizes the **same** Jules session as the Architect to save context window overhead. It sends a follow-up message: "You are now acting as the Red Team Critic. Evaluate the above architecture against these criteria: [Checklist]. Return your findings." This maintains continuity and efficiency.

## Implementation Approach
1. **Prompts Creation:** Write `ARCHITECT_CRITIC_INSTRUCTION.md` with explicit anti-pattern rules.
2. **Service Implementation:** Create `src/services/self_critic_evaluator.py`. It reads the generated `SYSTEM_ARCHITECTURE.md` and `SPEC.md` files (or directly from LangGraph state). It sends the fixed evaluation prompt to the existing Architect session.
3. **Graph Modification:** In `src/graph.py`, modify `_create_architect_graph` to transition from `architect_session` to `architect_critic`.
4. **Routing Logic:** Add `route_architect_critic` in `src/graph_nodes.py`.
   - If `CriticResult.is_approved` is `True`, go to `END`.
   - If `False`, go back to `architect_session` with feedback injected into the next prompt.
5. **Session Management:** Ensure the Jules session state handles the follow-up effectively without resetting. Add retry limits (e.g., max 3 self-critic loops) to prevent infinite loops.

## Test Strategy
### Unit Testing Approach
- Develop `test_self_critic_evaluator.py`. Mock the Jules API response to return both an approved `CriticResult` and a rejected one with a list of vulnerabilities.
- Ensure the `self_critic_evaluator.py` correctly parses the JSON output from Jules and maps it to the Pydantic model without crashing if the AI outputs extraneous text.
- Assert that the fixed prompts (`ARCHITECT_CRITIC_INSTRUCTION.md`) are successfully loaded and template variables are substituted.

### Integration Testing Approach
- Mock the LangGraph `ainvoke` for the Architect graph. Assert the sequence `START` $\rightarrow$ `architect_session` $\rightarrow$ `architect_critic` $\rightarrow$ `END` occurs for a "perfect" spec.
- Assert that a rejected spec loops back to `architect_session` with the `vulnerabilities` string concatenated to the prompt history.