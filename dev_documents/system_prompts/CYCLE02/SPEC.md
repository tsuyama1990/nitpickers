# CYCLE02 SPEC: GitHub Read-Only Operations Transition

## Summary
The primary objective of CYCLE02 is to securely transition all read-only repository interactions (e.g., fetching file contents, querying issue details, analyzing commit histories) from the legacy, fragile custom Python wrappers to the standardized `@modelcontextprotocol/server-github`. This cycle builds upon the infrastructure established in CYCLE01 by extending the `McpClientManager` to simultaneously manage a new GitHub Stdio sidecar process. Crucially, this cycle enforces the Principle of Least Privilege: analytical nodes like the `Architect` and `Auditor` will now be dynamically bound *only* to read-safe tools (`get_file_content`, `search_repositories`), entirely removing the prompt-based reliance on the Python backend to supply hard-coded context. This significantly reduces the token bloat and hallucination risk associated with massive Pydantic response parsing, while preparing the system for the high-risk write operations in CYCLE03.

## System Architecture
The architecture expands the `McpClientManager` to act as a true router, concurrently managing the established E2B server and the new GitHub server. The key architectural shift is within the LangGraph nodes themselves. The `src/nodes/architect.py` and `src/nodes/auditor.py` (and relevant QA/Review nodes) are refactored to query the manager for the `github` tools. The system must filter out destructive write tools (like `push_commit` or `create_pull_request`) before binding them to these specific nodes. The legacy wrappers located in `src/services/git_ops.py` (specifically read methods) will begin deprecation, paving the way for their complete removal in CYCLE03. The fundamental Pydantic structures of the workflow remain undisturbed.

```text
/
├── pyproject.toml
├── src/
│   ├── nodes/
│   │   ├── **architect.py**           [MODIFIED]
│   │   ├── **auditor.py**             [MODIFIED]
│   │   └── sandbox_evaluator.py
│   └── services/
│       ├── **mcp_client_manager.py**  [MODIFIED]
│       └── git_ops.py                 [PARTIALLY DEPRECATED]
```

## Design Architecture
This refactoring centers on the correct binding and strict filtering of the tool schemas natively returned by the `@modelcontextprotocol/server-github` via the `McpClientManager`.

**Domain Concepts & Core Mappings:**
The core concept is that a "read" action is no longer a blocking, deterministic Python function call that injects massive text blocks directly into the LLM prompt. Instead, the LLM autonomously decides *which* files to read using the `get_file_content` tool natively, allowing it to explore the repository dynamically during its reasoning loops. The `ToolMessage` result natively populates the context window.

**Key Invariants & Constraints:**
1.  **Principle of Least Privilege (Mechanical Gates):** The `McpClientManager` (or a dedicated proxy layer within it) MUST provide a mechanism to filter the tools returned from a server. The `Architect` and `Auditor` nodes must physically lack access to any tool that can mutate the repository state (e.g., `create_branch`, `push_commit`). This invariant must be mechanically enforced in code, not merely suggested via prompt engineering.
2.  **Token Exhaustion Prevention (Pagination Proxy):** The raw `get_file_content` MCP tool returns entire files. To prevent context window crashes, the `McpClientManager` must implement an interception or wrapper layer around this specific tool before returning it to LangChain. This wrapper must enforce parameters like `start_line` and `end_line`, and strictly truncate the returned `ToolMessage` payload if it exceeds a predefined maximum character limit (e.g., 50,000 chars), effectively acting as a safe pagination proxy.
3.  **Graceful Fallbacks (Error Handling):** The GitHub MCP Server returns structured JSON-RPC errors when files are missing or endpoints fail. The LangGraph nodes must be configured to correctly parse these standard `ToolMessage` errors into the designated Pydantic `ToolExecutionError` without crashing the entire state machine, allowing the LLM to gracefully recover.
4.  **Authentication Isolation:** The `GITHUB_PERSONAL_ACCESS_TOKEN` must be strictly managed by the `McpClientManager` during the Stdio initialization of the sidecar, completely isolating it from the LLM execution environment or the node logic.

## Implementation Approach
1.  **Extend McpClientManager:** Modify `src/services/mcp_client_manager.py` to asynchronously connect to a second server: `npx -y @modelcontextprotocol/server-github`, securely passing the `GITHUB_PERSONAL_ACCESS_TOKEN`. Ensure connection pooling correctly handles both E2B and GitHub concurrently via the `async with` singleton pattern.
2.  **Implement Tool Filtering & Proxy:** Add a method to the `McpClientManager` (e.g., `get_readonly_tools(server_name)`) that explicitly filters the retrieved tools against a strict whitelist (e.g., `['get_file_content']`). Implement the Token Exhaustion Prevention logic by injecting a wrapper around the `get_file_content` schema that enforces truncation.
3.  **Refactor Analytical Nodes:** Update `src/nodes/architect.py` and `src/nodes/auditor.py`. Retain critical deterministic context (like loading explicit `ALL_SPEC.md`), but inject the `McpClientManager`, retrieve the safely proxied read-only tools, and run a pre-processing autonomous LLM exploration loop.
4.  **ReAct Execution Abstraction:** Delegate the ReAct while-loop mapping logic (binding, tool execution, payload appending) into a shared `src/services/react_agent.py` to preserve DRY boundaries across nodes that invoke tools natively (Architect and LLMReviewer).
5.  **State Transformation & Fallback Logic:** Ensure the nodes correctly process the `ToolMessage` returned by the GitHub server, particularly when handling `mcp.ServerError` (e.g., File Not Found), allowing the LLM to continue its reasoning loop securely.

## Test Strategy

**Unit Testing Approach:**
The primary unit testing focus will be on the newly implemented tool filtering logic and graceful error handling.
-   Update `tests/unit/test_mcp_client_manager.py` to verify that `get_readonly_tools()` correctly strips destructive tools (e.g., `push_commit`) from a mocked tool schema returned by the Stdio connection. This mechanically enforces the Principle of Least Privilege.
-   Refactor `tests/unit/test_architect.py`. Mock the `McpClientManager` to return the `get_file_content` tool. Assert that the node successfully binds the tool and correctly formats the simulated `ToolMessage` containing file contents back into the `CycleState`.

**Integration Testing Approach:**
Integration testing must ensure the analytical nodes correctly utilize the standardized protocol and handle common errors without crashing.
-   Implement `tests/ac_cdd/integration/test_mcp_github_read_fallback.py`.
-   This test must configure the LangGraph engine with the `McpClientManager` pointing at a local mock GitHub server or a dedicated test repository.
-   **Crucial Assertion:** The test must pass a `CycleState` requesting a file that deliberately does not exist. It must verify that the `Architect` node successfully triggers the `get_file_content` tool, the server returns an accurate "file not found" `ToolMessage`, and the LLM natively recovers from the error without the system raising a fatal `ValueError` or crashing the graph execution.
