<thought>
**Architectural Stress Test & Reasoning Protocol:**

*Global Consistency (SYSTEM_ARCHITECTURE.md)*
-   **Requirement Check:** `ALL_SPEC.md` requires replacing manual API wrappers with an "MCP Router" utilizing `@modelcontextprotocol/server-github`, `@e2b/mcp-server`, and `@google/jules-mcp` via the `mcp` and `langchain-mcp-adapters` SDKs.
-   **Stress Test:**
    -   *Edge Case 1: Token Exhaustion.* The GitHub MCP's `get_file_content` will return the entire file. If an agent requests `package-lock.json`, the LLM context window blows up, crashing the graph. The current architecture mentions prompt engineering guardrails, but mechanical truncation or pagination within the `McpClientManager` is a safer architectural guarantee.
    -   *Edge Case 2: Stdio Zombie Processes.* The `McpClientManager` initializes Node.js subprocesses via Stdio. If the LangGraph execution crashes unexpectedly, do these processes become zombies? We need explicit context managers (`async with`) and explicit lifecycle shutdown hooks in the architecture.
    -   *Edge Case 3: Concurrency/Race Conditions.* Cycle 03 uses Jules MCP for "parallel agent dispatching". If multiple agents return diffs simultaneously, how does the `Global Refactor` node deterministically merge them into `CycleState` without race conditions? The Pydantic domain models must enforce sequential patching or lock mechanisms.

*Cycle Precision (SPEC.md / UAT.md)*
-   **CYCLE01 (E2B):** The current plan introduces `McpClientManager`. However, the exact configuration of `StdioServerParameters` and how the LangGraph node *persists* the connection across ticks without re-initializing the Node process every time is vague. The `McpClientManager` must be defined as a long-lived async dependency injected into the node execution context.
-   **CYCLE02 (GitHub Read):** Fails to explicitly define how to handle large files. The `SPEC.md` needs to enforce a parameter wrapper around the raw MCP tool to require line numbers or chunking.
-   **CYCLE03 (GitHub Write/Jules):** The transition from local `subprocess` Git commits to remote MCP commits changes the state model. The system must now track remote PR links instead of local branch SHAs. The `SPEC.md` needs to update the Pydantic `CycleState` field definitions to match this new reality.

*Code Design Foundation (Pydantic Schemas)*
-   The current specs vaguely say "use existing schemas". This isn't "Schema-First". I must explicitly define the interface of `McpClientManager` and how it wraps `mcp.ClientError` into domain-specific Pydantic models (e.g., `ToolExecutionError(BaseModel)`).

*Alternative Approaches Evaluated:*
-   *Alternative 1: HTTP/SSE MCP Servers.* Instead of Stdio, run the MCP servers as separate Docker containers communicating via HTTP SSE.
    -   *Rejection Reason:* Adds immense network latency to every tool call, complicates Docker-compose topology unnecessarily, and introduces network security vulnerabilities. Stdio is strictly superior for local sidecars.
-   *Alternative 2: Custom LangChain Tools vs. Native MCP Binding.* Manually parsing the MCP schema and building `langchain.tools.Tool` objects.
    -   *Rejection Reason:* `langchain-mcp-adapters` handles this natively. Custom translation adds the exact middleware we are trying to eliminate.

*Conclusion of Optimal Approach:*
The overall "MCP Router via Stdio" is optimal, but the architectural documents lack critical defensive engineering mechanisms (zombie process management, token pagination, race condition handling) and precise schema definitions. I must adjust the architecture and cycle plans to inject these specific, hardened implementation details.
</thought>

# Architect Critic Review: Structural Analysis & Refinement

## 1. Verification of the Optimal Approach

The core architectural paradigm—transitioning from legacy Python API wrappers to an "MCP Router" model utilizing Stdio sidecars—is the optimal approach for resolving the fragility and maintenance overhead outlined in `ALL_SPEC.md`.

**Alternative Approaches Considered & Rejected:**
1.  **HTTP/SSE Transport Layer:** Running the MCP servers as fully isolated, network-addressable containers communicating via HTTP Server-Sent Events (SSE).
    *   *Why Rejected:* While this provides absolute container isolation, it introduces significant network latency to the inner-loop reasoning cycles of the LLM. It also vastly complicates the `docker-compose.yml` topology and requires securing internal container networks. The selected **Stdio Transport Layer** is strictly superior for this use case: it is zero-latency, highly secure (no exposed ports), and tightly couples the sidecar lifecycle to the main Python process.
2.  **Manual Schema Translation:** Writing custom Python adapters to translate the JSON-RPC schemas returned by the MCP servers into standard LangChain `Tool` objects.
    *   *Why Rejected:* This simply replaces one form of brittle middleware with another. Relying strictly on the official `langchain-mcp-adapters` library guarantees that the LLM's native Function Calling capabilities are directly and safely wired to the MCP server's advertised schemas without manual interference.

**Architectural Stress Test Findings (Vulnerabilities Addressed):**
While the high-level approach is sound, the initial `SYSTEM_ARCHITECTURE.md` lacked several critical defensive engineering mechanisms:
*   **Vulnerability 1: Token Context Exhaustion.** The raw GitHub MCP `get_file_content` tool returns entire files. An agent requesting a minified build artifact or `package-lock.json` will instantly crash the LLM context window.
    *   *Correction:* The `McpClientManager` must implement an interception layer or middleware that wraps the raw MCP tools to enforce pagination, line-number bounds, or hard token limits before injecting the result into the LangGraph state.
*   **Vulnerability 2: Stdio Zombie Processes.** If the Python LangGraph engine crashes or is forcefully terminated during a cycle, the child Node.js processes (`npx`) could become orphaned zombies consuming host memory.
    *   *Correction:* The architecture must explicitly mandate the use of `async with` context managers and aggressive `__aexit__` teardown hooks within the `McpClientManager` to guarantee process termination.
*   **Vulnerability 3: Parallel Session Race Conditions.** Cycle 03 relies on Jules MCP for parallel fleet dispatching. If multiple agents return conflicting codebase diffs simultaneously, the `CycleState` could become corrupted.
    *   *Correction:* The `Global Refactor` node must employ deterministic, sequential conflict resolution parsing (e.g., using `FilePatch` Pydantic models) rather than blindly appending results to the state.

## 2. Precision of Cycle Breakdown and Design Details

The cycle breakdown (01: Sandboxing, 02: Read-Only Git, 03: Write Git & Fleet) is logically sound and adheres to the strangler fig pattern, ensuring safe, incremental migration. However, the initial specifications lacked "Schema-First" precision.

**Adjustments Mandated for Specific Cycles:**

*   **CYCLE01 Adjustments:** The specification must explicitly define the Pydantic configuration schema for the `McpClientManager`. It must detail the asynchronous singleton pattern required to inject the connection pool into the LangGraph nodes without re-initializing the Node.js process on every graph tick.
*   **CYCLE02 Adjustments:** The specification must explicitly define the mechanical filters used to strip destructive tools (Principle of Least Privilege). Furthermore, it must detail the error-handling schemas required to catch `mcp.ServerError` natively and map it to a user-friendly `ToolExecutionError` model.
*   **CYCLE03 Adjustments:** The design must account for the state paradigm shift. Legacy local git operations tracked local branch SHAs. The new MCP operations mutate remote states directly. The Pydantic `CycleState` models must be updated in the specification to reflect tracking remote `Pull Request URLs` and remote `Commit Hashes` instead of local file paths.

I will now proceed to implement these structural refinements across the `SYSTEM_ARCHITECTURE.md` and the respective cycle `SPEC.md` and `UAT.md` files.
