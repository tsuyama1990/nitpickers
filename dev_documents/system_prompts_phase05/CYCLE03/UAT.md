# Cycle 03: User Acceptance Testing (GitHub Write & Jules Orchestration)

## Test Scenarios

### SCN-03-01: GitHub MCP Write & Pull Request Generation
- **Priority**: High
- **Description**: Verify that the `master_integrator` agent natively uses `push_commit` and `create_pull_request` to submit validated changes to the target repository.
- **User Experience**: The system automatically and successfully opens a valid Pull Request on GitHub, containing correctly merged code and descriptive commit messages, without manual backend `git push` executions.

### SCN-03-02: Parallel Agent Session Orchestration via Jules MCP
- **Priority**: High
- **Description**: Verify that the `global_refactor` agent natively calls `create_session` and `dispatch_workers` via the `@google/jules-mcp` server, correctly spawning cloud agents to process files in parallel.
- **User Experience**: Complex, repository-wide refactoring tasks are dispatched quickly and reliably, and the main system waits for standard MCP ToolMessage updates rather than aggressively polling legacy HTTP endpoints.

### SCN-03-03: Conflict Resolution & Robustness
- **Priority**: Critical
- **Description**: Verify that the `master_integrator` correctly handles GitHub MCP tool errors returned when encountering Git merge conflicts, autonomously falling back to manual resolution or requesting a fresh branch rebase.
- **User Experience**: Even when a parallel commit breaks the branch state, the agent parses the `stderr` correctly and gracefully orchestrates a fix, preventing pipeline crashes.

### SCN-03-04: Mechanical Gate Verification (Security Check)
- **Priority**: Critical
- **Description**: Ensure that write tools (`push_commit`, `create_pull_request`) are strictly walled off from read-only nodes (e.g., `auditor.py`, `architect.py`), preventing hallucinated destructive actions.

## Behavior Definitions

### Feature: MCP GitHub Write & Jules Orchestration

**Scenario: Master Integrator Successfully Opens a Pull Request**
- **GIVEN** a successfully validated code change in Cycle 02
- **AND** the `master_integrator` agent is initialized with bound GitHub write tools
- **WHEN** the agent reaches the submission step
- **THEN** it must execute a `ToolCall` for `push_commit` followed by `create_pull_request`
- **AND** the mock GitHub server must return a successful PR URL payload
- **AND** the system must transition to the completed state

**Scenario: Global Refactor Successfully Dispatches Parallel Agents**
- **GIVEN** a large-scale refactoring requirement
- **AND** the `global_refactor` agent is initialized with bound Jules MCP tools
- **WHEN** the agent processes the requirement
- **THEN** it must execute a `ToolCall` for `create_session`
- **AND** the tool execution must return a successful session ID
- **AND** the agent must handle standard server events representing worker diffs

**Scenario: Master Integrator Gracefully Handles Merge Conflicts**
- **GIVEN** the Master Integrator agent executing a `push_commit` on a stale branch
- **WHEN** the MCP server returns a push rejection (merge conflict) string
- **THEN** the agent must not crash due to unhandled exceptions
- **AND** the agent must natively extract the error message and re-evaluate its branching strategy

**Scenario: Mechanical Gate Precludes Write Execution**
- **GIVEN** an attempt to invoke `push_commit` from the `QA` or `Auditor` node
- **WHEN** the action is initiated
- **THEN** the system must strictly reject the tool invocation or ensure the tool is simply absent from the node's toolset, logging a security blockade.