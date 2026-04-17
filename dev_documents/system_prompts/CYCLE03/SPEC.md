# CYCLE03: Phase 3 Integration Graph & Conflict Manager

## Summary
CYCLE03 introduces the independent `Integration Phase` graph. This centralizes code merging across parallel cycles and upgrades the AI `ConflictManager` to utilize a deterministic 3-way Git diff prompt, ensuring safer, context-aware conflict resolution.

## Infrastructure & Dependencies

### A. Project Secrets (`.env.example`)
- Target Project Secrets:
  - `JULES_API_KEY`: Required for the `master_integrator_node`.

### B. System Configurations (`docker-compose.yml`)
- No new environment variables needed for Docker compose in this cycle.

### C. Sandbox Resilience
- **Mandate Mocking**: The `git show` subprocess commands and the LLM API call within the `build_conflict_package` MUST be mocked in tests to ensure deterministic validation without requiring a live, conflicted Git repository.

## System Architecture

Modifications target the conflict service and add a new integration graph definition.

```text
nitpickers/
└── src/
    ├── **graph.py**
    └── services/
        └── **conflict_manager.py**
```

## Design Architecture

- **`src/services/conflict_manager.py`**:
  - `build_conflict_package`: Overhauled to execute `git show :1:{file}`, `:2:{file}`, and `:3:{file}` to extract the Base, Local, and Remote code blocks.
  - Generates a fixed-format prompt presenting these three distinct blocks to the Master Integrator LLM, instead of passing raw standard conflict markers.
- **`src/graph.py` (`_create_integration_graph`)**:
  - A new, independent graph definition.
  - Nodes: `git_merge_node`, `master_integrator_node`, `global_sandbox_node`.
  - Edges: Loops `master_integrator_node -> git_merge_node` on conflict. Routes to `global_sandbox_node` on success.

## Implementation Approach

1.  Open `src/services/conflict_manager.py`. Rewrite `build_conflict_package` to use subprocess calls for `git show :1:`, `:2:`, and `:3:`.
2.  Update the returned prompt string to format as: "### Base\n...\n### Branch A\n...\n### Branch B\n...".
3.  Open `src/graph.py`. Define `_create_integration_graph`.
4.  Implement `route_merge` to transition based on "conflict" or "success".
5.  Implement `route_global_sandbox` to bounce back to `master_integrator_node` if integration introduces syntax/type regressions.

## Test Strategy

### Unit Testing Approach
- Mock `subprocess.check_output` (or the internal Git ops tool) within tests for `build_conflict_package`. Assert that the returned string correctly embeds the mocked Base, Local, and Remote text blocks in the expected markdown format.

### Integration Testing Approach
- Compile `_create_integration_graph`. Mock the Git merge node to return "conflict", the master integrator to return "success", and the global sandbox to return "pass". Verify the correct topological transition path.