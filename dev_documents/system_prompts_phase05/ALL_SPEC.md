Requirement Definition: MCP Architecture Integration for Nitpickers

1. Project Overview

Objective: Refactor the core infrastructure of the nitpickers repository to natively utilize the Model Context Protocol (MCP) for all external environment interactions. This specifically targets GitHub (Version Control), E2B (Cloud Sandboxing), and Jules (Agent Fleet & Session Orchestration).

Goal: Substantially reduce the codebase's maintenance overhead and technical debt, improve the overall robustness of the multi-agent system, and transition the Python backend from managing brittle, raw API requests (acting as an "API Wrapper") to dynamically routing standardized tools directly to the LLM agents (acting as an "MCP Router").

Context & Rationale: The nitpickers system currently orchestrates a complex, 8-cycle multi-agent workflow (Cycles 01-08) involving specialized nodes: an Architect, Coder, Auditor, Master Integrator, and Sandbox Evaluator. As the system scales and the complexity of these cycles increases, manually wrapping REST APIs and proprietary SDKs (like e2b and github endpoints) within custom Python services has proven severely fragile.

Upstream API changes break custom parsers, and injecting state manually requires bloated, hard-coded prompt engineering. By adopting an MCP architecture, we delegate the heavy lifting of tool execution, payload formatting, authentication, and standard error handling to standardized, vendor-maintained MCP servers. This allows the core Python codebase to focus exclusively on what it does best: multi-agent orchestration, state management, and graph logic using LangGraph.

2. Architectural Paradigm Shift

2.1 Current Architecture (The Legacy "API Wrapper" Approach)

In the current implementation, the Python application acts as a heavy intermediary (middleware) between the AI models and the external world. This tightly couples the business logic with infrastructure concerns.

Rigid Tool Definitions: Developers must manually write complex Pydantic models or JSON schemas to describe tools to the LLM. If GitHub adds a new parameter to their Pull Request API, the Pydantic schema in Python must be manually updated.

Manual Orchestration: LLMs generate JSON payloads based on custom system prompts (e.g., CODER_INSTRUCTION.md). Python services like src/services/git_ops.py and src/services/e2b_executor.py must intercept this JSON, perform validation, format it into raw HTTP requests or proprietary SDK calls, and execute them over the network.

Context Injection: Responses from these APIs must be manually parsed, formatted into readable markdown or text, and injected back into the LLM's prompt context window. This often results in token bloat.

Pain Points: * High Maintenance: Every new operational feature requires updating the prompt, the tool schema, the response parser, and the execution logic.

Fragility: Unpredictable edge cases in API responses (like obscure Git merge conflicts, E2B timeout stack traces, or Jules session drops) often break the custom parsing logic, crashing the entire agent cycle.

Authentication Sprawl: API keys (GITHUB_TOKEN, E2B_API_KEY) must be managed and injected at the request level throughout various deeply nested Python service classes.

2.2 New Architecture (The "MCP Router" Approach)

The MCP architecture fundamentally decouples the LLM from the underlying API mechanics by introducing the universal JSON-RPC 2.0 standard directly to the AI model.

Sidecar Servers: Three standalone Node.js MCP Server sidecars are introduced to the Docker environment, running as long-lived background subprocesses communicating via the stdio transport layer.

Dynamic Discovery: The Python application uses an MCP Client (such as Anthropic's official mcp Python SDK and LangChain's langchain-mcp-adapters) to connect to these servers. The servers automatically advertise their available tools, semantic descriptions, and strongly-typed required schemas directly to the LLM upon initialization.

Native Execution: The LLM natively generates tool calls via its built-in Function Calling capabilities. The MCP client transparently forwards these calls to the sidecar server. The server securely executes the logic (e.g., running a sandboxed bash command in E2B or committing a file payload to GitHub) and returns a natively formatted context payload directly back to the LLM.

Benefits: Complete elimination of repetitive boilerplate code. The LLM exclusively handles the "what to do," the MCP server robustly handles the "how to do it," and the Python graph simply wires the network topologies together.

3. Scope of Work

3.1 In-Scope Implementations

GitHub MCP Server (@modelcontextprotocol/server-github):

Target Nodes: Bound to the master_integrator, architect, and coder nodes.

Capabilities: Handles reading repository structures, fetching file contents, querying issues, creating branches, pushing commits, and generating Pull Requests.

E2B MCP Server (@e2b/mcp-server):

Target Nodes: Bound to the sandbox_evaluator and qa nodes.

Capabilities: Manages ephemeral cloud sandboxed code execution, safe bash command execution, filesystem modifications within the sandbox, and isolated unit testing.

Jules MCP Server (@google/jules-mcp):

Target Nodes: Bound to the global_refactor and audit_orchestrator components.

Capabilities: Handles scaling dynamic agent fleets, dispatching distributed worker sessions, tracking session telemetry, and performing complex multi-file reconciliation across a repository.

Infrastructure Setup: Updating docker-compose.yml and Dockerfile to manage the Node.js runtime, ensuring local dependencies for the MCP sidecar lifecycles via stdio are met.

LLM Tool Binding: Deep refactoring of the LangGraph/Agent nodes in src/nodes/*.py to bind MCP tools dynamically using .bind_tools().

3.2 Out-of-Scope Configurations

To ensure a safe, deterministic, and stable migration, the following items are strictly deferred to future phases:

Memory MCP / Knowledge Graph Integrations: Replacing the core file-based state management (e.g., dev_documents/system_prompts_phase04/project_state.json, ALL_SPEC.md). The existing src/state_manager.py and src/state_validators.py will continue to handle inter-cycle state persistence.

Web Search / Browser Automation MCPs: Introducing external internet access via tools like Puppeteer or Brave Search introduces non-deterministic behavior and broad security risks that require a separate, extensive evaluation phase.

Workflow Alterations: Altering the fundamental 8-cycle multi-agent workflow. The architectural transition between Cycles 01 through 08 must remain conceptually and functionally identical to the end user.

4. Component Refactoring Plan

4.1 GitHub Operations Refactoring

Goal: Completely delegate all Git state tracking, branch creation, pulling, pushing, and PR management to the official GitHub MCP server.

Additions:

Initialize @modelcontextprotocol/server-github within the new MCP client manager.

Map tools such as get_file_content, create_branch, push_commit, and create_pull_request to specific agent nodes based on their strict required permissions (e.g., architect is read-only, master_integrator is write-enabled).

Required Environment Variable: GITHUB_PERSONAL_ACCESS_TOKEN.

Deprecations / Deletions (High Volume):

src/services/git_ops.py (Delete entirely)

src/services/git/base.py (Delete entirely)

src/services/git/branching.py (Delete entirely)

src/services/git/checkout.py (Delete entirely)

src/services/git/merging.py (Delete entirely)

src/services/git/state.py (Delete entirely)

src/services/integration_usecase.py (Substantially refactor to remove manual git subprocess orchestrations; replace with MCP router logic mapping).

4.2 E2B Sandbox Refactoring

Goal: Delegate deterministic code execution, bash environment interactions, and test suite evaluations entirely to the E2B MCP server, preventing the LLM from hallucinating output formats or requiring custom SDK wrappers.

Additions:

Initialize @e2b/mcp-server.

Expose the run_code and execute_command tools primarily to src/nodes/sandbox_evaluator.py and src/nodes/qa.py.

Required Environment Variable: E2B_API_KEY.

Deprecations / Deletions:

src/contracts/e2b_executor.py (Delete entirely)

src/services/e2b_executor.py (Delete entirely)

src/sandbox.py (Delete entirely)

src/services/sandbox/sync.py (Delete entirely)

Remove any logic manually parsing stdout/stderr from standard shell executions.

4.3 Jules Session Orchestration Refactoring

Goal: Delegate ephemeral agent sessions, cloud workspace synchronization, and parallel agent dispatching to the Jules MCP.

Additions:

Connect to @google/jules-mcp.

Bind orchestration tools (create_session, review_changes, list_sessions) to higher-level orchestrator nodes like src/nodes/global_refactor.py.

Required Environment Variable: JULES_API_KEY.

Deprecations / Deletions:

src/services/jules/api.py (Delete entirely)

src/services/jules_client.py (Delete entirely)

src/services/jules/session.py (Delete entirely)

src/jules_session_state.py (Refactor to remove manual HTTP polling and pagination loops; rely on MCP tool execution states and Server-Sent Events if applicable).

5. Technical Requirements & Implementation Details

5.1 Infrastructure Changes (Dockerfile & docker-compose.yml)

The selected MCP servers operate as Node.js processes. To communicate via the highly efficient stdio (Standard Input/Output) transport layer, the main Python container must be capable of launching Node applications via npx without cross-container network latency.

Update the main Dockerfile:

# Add Node.js runtime to the existing Python environment
RUN apt-get update && apt-get install -y ca-certificates curl gnupg
RUN curl -fsSL [https://deb.nodesource.com/setup_18.x](https://deb.nodesource.com/setup_18.x) | bash -
RUN apt-get install -y nodejs

# Pre-install MCP servers globally to lock versions, prevent runtime downloading,
# and drastically improve agent startup speeds
RUN npm install -g @modelcontextprotocol/server-github @e2b/mcp-server @google/jules-mcp


5.2 Python Dependencies (pyproject.toml)

Add the required communication adapters to bridge the LangGraph agents to the standard MCP servers.

[tool.poetry.dependencies]
mcp = "^1.0.0"
langchain-mcp-adapters = "^0.1.0" # Crucial for seamlessly binding tools to LangGraph models


5.3 MCP Client Manager (src/mcp_client_manager.py)

A new singleton or dependency-injected managed service must be created to handle the lifecycle of the MCP subprocesses. This manager ensures they boot sequentially when the system starts and terminate cleanly without zombie processes when execution finishes.

Key Responsibilities:

Securely load .env credentials dynamically.

Manage concurrent connection pooling using the StdioServerParameters implementation.

Expose standardized get_tools() interfaces to retrieve tool lists for dynamic agent initialization.

Conceptual Implementation Snippet:

import os
from mcp import StdioServerParameters
from langchain_mcp_adapters.client import MultiMCPClient

async def initialize_mcp_clients() -> MultiMCPClient:
    client = MultiMCPClient()
    
    # 1. Initialize GitHub MCP (Using pre-installed global npm package)
    await client.connect(
        "github",
        StdioServerParameters(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")}
        )
    )
    
    # 2. Initialize E2B MCP
    await client.connect(
        "e2b",
        StdioServerParameters(
            command="npx",
            args=["-y", "@e2b/mcp-server"],
            env={"E2B_API_KEY": os.getenv("E2B_API_KEY")}
        )
    )
    
    return client

# Typical Usage in a LangGraph Node (e.g., src/nodes/coder.py)
# tools = await client.get_tools()
# agent_with_tools = llm.bind_tools(tools)


6. Migration Strategy (Phased Approach)

A "big bang" rewrite poses an unacceptable risk to the integrity of the 8-cycle workflow. The migration will follow a strict strangler fig pattern, replacing domains sequentially and relying heavily on the existing test suites (e.g., tests/ac_cdd/integration/test_end_to_end_workflow.py).

Phase 0: Infrastructure Prep & Tool Discovery Validation

Update Dockerfile and pyproject.toml.

Implement src/mcp_client_manager.py.

Exit Criteria: Verify that the Docker container can successfully spin up the MCP stdio processes, fetch the complete tool schemas, and log them without blocking the main asyncio event loop.

Phase 1: E2B Sandbox Isolation (Low Impact, High Yield)

Inject the E2B MCP tools into the sandbox_evaluator.py agent.

Update the QA_AUDITOR_INSTRUCTION.md and UAT_AUDITOR_INSTRUCTION.md prompts to explicitly instruct the agent to use the provided run_code MCP tool instead of generating custom JSON payloads.

Exit Criteria: tests/unit/test_sandbox_evaluator.py and tests/unit/test_e2b_executor.py (rewritten for MCP) pass reliably. The evaluator can read test failures and output logic correctly via MCP context.

Cleanup: Delete src/contracts/e2b_executor.py.

Phase 2: GitHub Read-Only Operations (Medium Impact)

Expose read-only tools (get_file_content, search_repositories) from the GitHub MCP to architect.py and auditor.py.

Remove prompt logic instructing the LLM to ask the custom Python backend for file contents. Let the LLM execute the tools autonomously during its reasoning loops.

Exit Criteria: Context injection matches the expectations of Cycle 01 and Cycle 02 in test_end_to_end_workflow.py.

Phase 3: GitHub Write Operations & Jules Orchestration (High Risk)

Refactor master_integrator.py to utilize create_pull_request and push_commit natively.

Refactor global_refactor.py and audit_orchestrator.py to dispatch and monitor parallel worker sessions via the Jules MCP.

Exit Criteria: End-to-end conflict resolution and branching logic works flawlessly in tests/ac_cdd/integration/test_git_robustness.py.

Cleanup: Conduct the final deletion of the src/services/git/ and src/services/jules/ directory trees.

7. Risk Management & Mitigation Strategies

While MCP drastically reduces custom Python code, delegating execution to black-box external servers introduces new operational risks that must be handled gracefully.

7.1 Context Window Exhaustion (Token Limits)

Risk: MCP tools execute dynamically. If an agent calls get_file_content on a massive, minified, or auto-generated file (e.g., package-lock.json), the MCP server will return it in its entirety, potentially blowing out the LLM's token limit and crashing the graph execution.

Mitigation: Implement strict prompt engineering guardrails in system prompts (e.g., ARCHITECT_INSTRUCTION.md), requiring the LLM to use line-number limits or chunking parameters when reading files. Alternatively, implement an interception/middleware layer in mcp_client_manager.py that truncates exceptionally large tool responses before they are injected into the LLM context.

7.2 Tool Hallucination & Security Escalation

Risk: The LLM might hallucinate an MCP tool schema, pass incorrect parameters, or attempt to call a destructive tool (e.g., push_commit to the main branch) prematurely before a review cycle is completed.

Mitigation: Rely on the Mechanical Gates tested in tests/unit/test_cycle03_mechanical_gate.py. Crucially, only bind destructive write tools to specific nodes (master_integrator.py) that are authorized to use them. Read-only nodes (architect.py) must be strictly supplied with read-only toolsets.

7.3 Debugging Opacity & Telemetry Loss

Risk: Because the communication happens over stdio binary streams rather than standard HTTP, tracing exactly what the LLM sent to the MCP server and what it received back becomes difficult, breaking the deep visibility required for LOG_ANALYSIS.md and test_execution_log.txt.

Mitigation: Utilize LangSmith, LangFuse, or custom LangChain callbacks within the mcp_client_manager.py to meticulously log the intermediate ToolCall and ToolMessage events natively within the LangGraph state execution.

8. Testing Strategy for Safe MCP Migration

To ensure the migration does not regress the highly stable 8-cycle architecture, a dedicated testing suite must be generated and executed prior to full deployment.

8.1 Unit Testing the MCP Router Components

The core logic shift requires new unit tests focused on tool binding and client initialization.

Target: tests/unit/test_mcp_client_manager.py (New File)

Strategy: Mock the StdioServerParameters to verify that the MultiMCPClient correctly discovers and registers tools from a mock stdio stream without making actual external network calls. Ensure timeout and retry mechanisms for server boot failures are active.

8.2 Integration Testing with Mock MCP Servers

To test the LangGraph nodes without exhausting API limits or mutating real repositories.

Target: tests/ac_cdd/integration/test_mcp_node_integration.py (New File)

Strategy: Create a lightweight, dummy Node.js MCP server that mimics the schemas of GitHub and E2B.

Specific Tests to Generate:

test_mcp_github_read_fallback(): Simulates a scenario where get_file_content fails (e.g., file not found). Verifies that the architect.py node gracefully handles the MCP error response and requests alternative context rather than crashing.

test_mechanical_gate_permissions(): Attempts to invoke a push_commit action from the auditor.py node, asserting that the tool execution is firmly rejected or omitted from the toolset.

8.3 End-to-End Shadow Testing

Ensure the functional parity of the new MCP Router vs. the legacy API Wrapper.

Target: tests/ac_cdd/integration/test_end_to_end_workflow.py

Strategy: Run the existing e2e test suite pointing the system at a dedicated, isolated test repository.

Specific Tests to Validate:

test_mcp_e2b_sandbox_execution(): Asserts that when the sandbox_evaluator generates a broken Python script, the E2B MCP tool correctly traps the exception and feeds the stderr back into the graph, resulting in a successful Cycle 04 failure categorization.

test_mcp_jules_session_dispatch(): Triggers a massive refactor that relies on global_refactor.py. Asserts that the Jules MCP correctly dispatches parallel agents and returns the reconciled session diffs without dropping state.

8.4 Rollback Protocol

If any End-to-End integration test fails critically due to an upstream MCP server bug:

Maintain the legacy src/services/ folders in a deprecated state (feature-flagged) for exactly one minor version release (e.g., v2.0-beta).

Configure src/config.py with an USE_LEGACY_API_WRAPPERS=True environment toggle that dynamically skips MCP tool binding and falls back to manual JSON schema prompts.


**BE CAREFUL ON APIKEY LEAKAGE**
during the last developments I got a notice from github as below:
So make sure the API key / token are not leaked via output texts etc...
Please resolve these alerts

Anyone with read access can view exposed secrets. Consider rotating and revoking each valid secret to avoid any irreversible damage.

GCP API Key Bound to a Service Account Review secret detected in ...ents/test_execution_log.txt#L1316 • commit 668952d0 OpenRouter API Key Review secret detected in ...ents/test_execution_log.txt#L1316 • commit 668952d0

this is because of you! I registered several apikeys to have you test with local enviroments.

in the other sessions, we you have already identified the issue. pls fix the problem as the branch is not integrated. pls make sure the problem is now completely fixed.

I've identified that the langchain-mcp-adapters library logs warnings that contain the complete environment when it detects unexpanded variables in environment variables like SUDO_COMMAND. Since SUDO_COMMAND contains commands with API keys injected via the environment in your specific setup, it leads to the keys being leaked into test logs.

I have updated the McpClientManager to sanitize the environment by actively filtering out variables starting with SUDO_ before passing them to the MCP sub-process. This prevents the warning and subsequent log leakage.

I am now returning to Phase 4 to finish removing legacy modules.

I understand the urgency and the API key leakage issue.

The leakage in test_execution_log.txt was caused by langchain-mcp-adapters logging the env dictionary when the MultiServerMCPClient is initialized with unexpanded environment variables like SUDO_COMMAND, which contained the injected test API keys.

I've already patched McpClientManager to sanitize os.environ before merging it into the subprocess config, ensuring SUDO_* commands (and thus the injected keys) are not passed or logged. I also removed the existing test_execution_log.txt which contained the leaked keys.

I am finalizing Phase 4 now (removing legacy modules completely) and will proceed to open the Pull Request immediately after resolving the remaining import errors.
