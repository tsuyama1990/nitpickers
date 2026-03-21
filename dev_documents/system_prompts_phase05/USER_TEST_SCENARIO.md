# User Test Scenario & Tutorial Strategy

## Tutorial Strategy

The primary goal of the User Acceptance Testing (UAT) tutorials is to visually and interactively verify that the Nitpickers multi-agent workflow successfully integrates the Model Context Protocol (MCP) Router paradigm. Users should be able to run a single executable file to observe the new architecture seamlessly replacing the legacy Python API wrappers without introducing regressions to the 8-cycle process.

To ensure reproducibility and ease of use, the UATs are implemented as executable Marimo notebooks (`.py`). Marimo allows developers to step through the UAT scenarios dynamically, providing immediate visual feedback for agent states and tool interactions.

### "Mock Mode" vs "Real Mode"

The tutorial strategy must support two distinct execution environments:

1. **Mock Mode (CI / No-API-Key Execution):**
   - **Purpose:** Fast, offline, and safe execution designed primarily for continuous integration (CI) or local environments where API keys (e.g., `E2B_API_KEY`, `GITHUB_PERSONAL_ACCESS_TOKEN`) are not available or where side effects are undesirable.
   - **Implementation:** The UAT will automatically instantiate local, dummy Node.js processes that mimic the `stdio` responses of `@e2b/mcp-server`, `@modelcontextprotocol/server-github`, and `@google/jules-mcp`. These mock servers will return static, successful payloads when agents emit `ToolCall` objects (e.g., returning mock file contents for `get_file_content` or mock stdout for `run_code`).
   - **Validation:** Ensures the Python `McpClientManager` correctly initializes standard I/O streams and LangGraph nodes bind the tools natively without crashing.

2. **Real Mode:**
   - **Purpose:** Full end-to-end validation using live external services to verify true integration and multi-modal diagnostic capture.
   - **Implementation:** Enabled when explicit `.env` configurations are provided. The UAT will initialize the genuine, globally installed MCP servers and execute actual sandbox evaluations and GitHub PR creations against a designated test repository.
   - **Validation:** Proves that the strangler fig migration is completely functional and the core workflow is preserved.

## Tutorial Plan

To maintain simplicity, we will create a **SINGLE** comprehensive Marimo notebook containing all scenarios.

**File:** `tutorials/mcp_architecture_verification.py`

This single file will sequentially walk the user through the following UAT scenarios corresponding to the three development cycles:

- **Phase 1: E2B Sandbox Isolation Verification**
  - Verify that the `McpClientManager` sanitizes the environment (explicitly checking that `SUDO_*` commands are dropped).
  - Verify that the `sandbox_evaluator` node natively invokes `run_code` and successfully processes mock/real stdout and stderr.

- **Phase 2: GitHub Read-Only Context Verification**
  - Verify that the `architect` node autonomously calls `get_file_content` without attempting to format custom JSON payloads.
  - Test graceful fallback mechanisms when the MCP server returns a `404 Not Found` for nonexistent files.

- **Phase 3: Write Operations & Security Gateway Verification**
  - Verify the mechanical gateway constraints: Attempt to inject `push_commit` capabilities into read-only nodes and assert failure.
  - Verify that the `master_integrator` successfully uses the native `create_pull_request` MCP tool.
  - Verify that the `global_refactor` node natively calls `create_session` via Jules MCP.

## Tutorial Validation

The `tutorials/mcp_architecture_verification.py` notebook must be strictly executable using the following command:

```bash
uv run marimo run tutorials/mcp_architecture_verification.py
```

**Validation Criteria:**
- The notebook executes sequentially without throwing internal unhandled exceptions.
- In Mock Mode, all assertions regarding tool binding and schema generation pass successfully.
- It dynamically imports the `src/` modules securely and gracefully handles any missing environment variables by falling back to mock servers.