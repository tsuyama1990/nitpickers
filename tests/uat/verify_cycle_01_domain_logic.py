import marimo

__generated_with = "0.10.14"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    mo.md(
        """
        # CYCLE01 UAT: Infrastructure Preparation & E2B Sandbox Isolation

        This notebook verifies the McpClientManager and its integration with the Sandbox Evaluator and QA nodes.
        """
    )
    return


@app.cell
def _():
    import os
    import pytest
    from unittest.mock import AsyncMock, patch

    from src.domain_models.config import McpServerConfig
    from src.services.mcp_client_manager import McpClientManager
    from src.nodes.sandbox_evaluator import SandboxEvaluatorNodes
    from src.state import CycleState
    from src.domain_models.execution import ToolExecutionError
    from src.enums import FlowStatus
    return (
        AsyncMock,
        CycleState,
        FlowStatus,
        McpClientManager,
        McpServerConfig,
        ToolExecutionError,
        SandboxEvaluatorNodes,
        os,
        patch,
        pytest,
    )


@app.cell
def _(mo):
    mo.md(
        """
        ## Scenario UAT-C01-01: Tool Discovery via Stdio Protocol

        Verifies `McpClientManager` establishes a connection to the MCP server and discovers tools.
        """
    )
    return


@app.cell
async def _(
    AsyncMock,
    McpClientManager,
    McpServerConfig,
    patch,
):
    _config = McpServerConfig(e2b_api_key="mock", npx_path="npx")
    _manager = McpClientManager(_config)

    with patch("src.services.mcp_client_manager.stdio_client") as _mock_stdio, \
         patch("src.services.mcp_client_manager.ClientSession") as _mock_session, \
         patch("src.services.mcp_client_manager.load_mcp_tools") as _mock_load_tools:

        _mock_stdio_cm = AsyncMock()
        _mock_stdio_cm.__aenter__.return_value = (AsyncMock(), AsyncMock())
        _mock_stdio.return_value = _mock_stdio_cm

        _mock_session_cm = AsyncMock()
        _mock_session_instance = AsyncMock()
        _mock_session_cm.__aenter__.return_value = _mock_session_instance
        _mock_session.return_value = _mock_session_cm

        _mock_tools = ["run_code", "execute_command"]
        _mock_load_tools.return_value = _mock_tools

        async with _manager as _connected_manager:
            _tools = await _connected_manager.get_tools()

            assert _tools == _mock_tools, "Failed to retrieve expected tools"
            print("✓ UAT-C01-01: Tool discovery successful.")
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Scenario UAT-C01-02: Native Code Execution via Tool Binding

        Verifies the `Sandbox Evaluator` evaluates a cycle correctly.
        """
    )
    return


@app.cell
async def _(
    AsyncMock,
    CycleState,
    FlowStatus,
    SandboxEvaluatorNodes,
    patch,
):
    _mock_process_runner = AsyncMock()
    _mock_process_runner.run_command.return_value = ("Success", "", 0, False)

    _mock_mcp_manager = AsyncMock()
    _mock_mcp_manager.__aenter__.return_value = _mock_mcp_manager
    _mock_mcp_manager.get_tools.return_value = ["run_code", "execute_command"]

    _node = SandboxEvaluatorNodes(mcp_manager=_mock_mcp_manager, process_runner=_mock_process_runner)
    _state = CycleState(cycle_id="01")
    _result = await _node.sandbox_evaluate_node(_state)

    assert _result["status"] == FlowStatus.READY_FOR_AUDIT, "Node failed mechanical blockade"
    assert "structural_report" in _result, "Missing structural report"
    print("✓ UAT-C01-02: Native evaluation successful.")
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Scenario UAT-C01-03: Robust Error Capture and State Mapping

        Verifies `Sandbox Evaluator` correctly captures failure states.
        """
    )
    return


@app.cell
async def _(
    AsyncMock,
    CycleState,
    FlowStatus,
    SandboxEvaluatorNodes,
):
    _mock_process_runner_err = AsyncMock()

    def _side_effect(cmd, **kwargs):
        if "test" in " ".join(cmd):
            return ("", "SyntaxError: invalid syntax", 1, False)
        return ("", "", 0, False)

    _mock_process_runner_err.run_command.side_effect = _side_effect

    _mock_mcp_manager_err = AsyncMock()
    _mock_mcp_manager_err.__aenter__.return_value = _mock_mcp_manager_err
    _mock_mcp_manager_err.get_tools.return_value = ["run_code"]

    _node_err = SandboxEvaluatorNodes(mcp_manager=_mock_mcp_manager_err, process_runner=_mock_process_runner_err)
    _state_err = CycleState(cycle_id="01")
    _result_err = await _node_err.sandbox_evaluate_node(_state_err)

    assert _result_err["status"] == FlowStatus.TDD_FAILED, "Node incorrectly passed mechanical blockade"
    assert "Verification failed" in _result_err["error"], "Error string missing failure notice"
    assert "SyntaxError: invalid syntax" in _result_err["error"], "Missing actual traceback in error"
    print("✓ UAT-C01-03: Robust error capture successful.")
    return


if __name__ == "__main__":
    app.run()
