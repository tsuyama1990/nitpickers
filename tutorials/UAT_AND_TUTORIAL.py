# mypy: ignore-errors
import marimo

__generated_with = "0.10.15"
app = marimo.App()


@app.cell
def mo_cell() -> tuple[object]:
    import marimo as mo

    return (mo,)


@app.cell
def intro_cell(mo: object) -> None:
    # Use generic object for mo to avoid mypy errors for dynamically imported marimo module
    if hasattr(mo, "md"):
        mo.md(
            """
            # CYCLE 02 UAT: Integration Graph & 3-Way Diff

            This notebook demonstrates the End-to-End User Acceptance Testing (UAT) scenarios for Phase 3 (Integration Graph) of the AC-CDD architecture.
            We will simulate integrating parallel feature branches, intelligent conflict resolution, and handling post-merge semantic failures using LangGraph.
            """
        )


@app.cell
def imports_cell() -> (
    tuple[object, object, object, object, object, object, object, object, object, object, object]
):
    import asyncio
    from pathlib import Path
    from unittest.mock import AsyncMock, MagicMock, patch

    from src.config import settings
    from src.graph import GraphBuilder
    from src.sandbox import SandboxRunner
    from src.service_container import ServiceContainer
    from src.services.jules_client import JulesClient
    from src.state import IntegrationState

    return (
        AsyncMock,
        GraphBuilder,
        IntegrationState,
        JulesClient,
        MagicMock,
        Path,
        SandboxRunner,
        ServiceContainer,
        asyncio,
        patch,
        settings,
    )


@app.cell
def setup_cell(  # type: ignore[no-untyped-def]
    GraphBuilder: object,  # noqa: N803
    JulesClient: object,  # noqa: N803
    MagicMock: object,  # noqa: N803
    SandboxRunner: object,  # noqa: N803
    ServiceContainer: object,  # noqa: N803
) -> tuple[object, object, object, object, object]:
    # Setup the mocked integration graph for UAT scenarios
    sandbox = MagicMock(spec=SandboxRunner)
    jules = MagicMock(spec=JulesClient)

    container = ServiceContainer.default()
    builder = GraphBuilder(container, sandbox, jules)
    integration_graph = builder.build_integration_graph()
    return builder, container, integration_graph, jules, sandbox


@app.cell
def scenario1_cell(  # type: ignore[no-untyped-def]
    IntegrationState: object,  # noqa: N803
    Path: object,  # noqa: N803
    asyncio: object,
    integration_graph: object,
    mo: object,
    patch: object,
    settings: object,
) -> tuple[bool, object, object, bool]:
    if hasattr(mo, "md"):
        mo.md("## Scenario 1: Clean Merge")

    async def run_scenario_1() -> tuple[object, bool, bool]:
        # Using a mock repository path to pass path validations
        repo_path = Path("/tmp/mock_repo")  # noqa: S108

        # We mock the internal node methods to simulate a clean merge
        with (
            patch.object(settings.paths, "workspace_root", repo_path),
            patch("os.getcwd", return_value=str(repo_path)),
            patch(
                "src.nodes.master_integrator.MasterIntegratorNodes.master_integrator_node"
            ) as mock_mi,
            patch(
                "src.nodes.sandbox_evaluator.SandboxEvaluatorNodes.sandbox_evaluate_node"
            ) as mock_sandbox,
            patch("src.services.git_ops.GitManager.merge_pr"),
        ):
            mock_sandbox.return_value = {"status": "pass"}

            state = IntegrationState(branches_to_merge=["clean-feature"])

            # Ainvoke the graph
            try:
                result = await integration_graph.ainvoke(
                    state, config={"configurable": {"thread_id": "uat_clean_merge"}}
                )
            except Exception as e:
                return str(e), False, False
            else:
                return result, mock_sandbox.called, mock_mi.called

    result_1, sandbox_called_1, mi_called_1 = asyncio.run(run_scenario_1())

    if hasattr(mo, "ui"):
        mo.ui.table(
            [
                {"Step": "Merge PR", "Expected": "Success", "Actual": "Success (Mocked)"},
                {
                    "Step": "Global Sandbox",
                    "Expected": "Called & Passed",
                    "Actual": f"Called: {sandbox_called_1}",
                },
                {
                    "Step": "Master Integrator",
                    "Expected": "Skipped",
                    "Actual": f"Called: {mi_called_1}",
                },
            ]
        )
    return mi_called_1, result_1, run_scenario_1, sandbox_called_1


@app.cell
def scenario2_cell(  # type: ignore[no-untyped-def]
    IntegrationState: object,  # noqa: N803
    Path: object,  # noqa: N803
    asyncio: object,
    integration_graph: object,
    mo: object,
    patch: object,
    settings: object,
) -> tuple[int, bool, object, object, bool]:
    if hasattr(mo, "md"):
        mo.md("## Scenario 2: Conflict Resolution via 3-Way Diff")

    async def run_scenario_2() -> tuple[object, bool, bool, int]:
        repo_path = Path("/tmp/mock_repo")  # noqa: S108

        with (
            patch.object(settings.paths, "workspace_root", repo_path),
            patch("os.getcwd", return_value=str(repo_path)),
            patch(
                "src.nodes.master_integrator.MasterIntegratorNodes.master_integrator_node"
            ) as mock_mi,
            patch(
                "src.nodes.sandbox_evaluator.SandboxEvaluatorNodes.sandbox_evaluate_node"
            ) as mock_sandbox,
            patch("src.services.git_ops.GitManager.merge_pr") as mock_merge,
        ):
            # Force the first merge to fail with conflict, then succeed
            mock_merge.side_effect = [Exception("conflict detected"), None]
            # Master integrator resolves the conflict
            mock_mi.return_value = {"unresolved_conflicts": []}
            # Sandbox passes
            mock_sandbox.return_value = {"status": "pass"}

            state = IntegrationState(branches_to_merge=["conflict-feature"])

            try:
                result = await integration_graph.ainvoke(
                    state, config={"configurable": {"thread_id": "uat_conflict"}}
                )
            except Exception as e:
                return str(e), False, False, 0
            else:
                return result, mock_sandbox.called, mock_mi.called, mock_merge.call_count

    result_2, sandbox_called_2, mi_called_2, merge_calls_2 = asyncio.run(run_scenario_2())

    if hasattr(mo, "ui"):
        mo.ui.table(
            [
                {"Step": "Merge PR attempts", "Expected": "2", "Actual": f"{merge_calls_2}"},
                {
                    "Step": "Master Integrator",
                    "Expected": "Called",
                    "Actual": f"Called: {mi_called_2}",
                },
                {
                    "Step": "Global Sandbox",
                    "Expected": "Called & Passed",
                    "Actual": f"Called: {sandbox_called_2}",
                },
            ]
        )
    return merge_calls_2, mi_called_2, result_2, run_scenario_2, sandbox_called_2


@app.cell
def scenario3_cell(  # type: ignore[no-untyped-def]
    IntegrationState: object,  # noqa: N803
    Path: object,  # noqa: N803
    asyncio: object,
    integration_graph: object,
    mo: object,
    patch: object,
    settings: object,
) -> tuple[bool, object, object, int]:
    if hasattr(mo, "md"):
        mo.md("## Scenario 3: Post-Merge Semantic Failure Recovery")

    async def run_scenario_3() -> tuple[object, int, bool]:
        repo_path = Path("/tmp/mock_repo")  # noqa: S108

        with (
            patch.object(settings.paths, "workspace_root", repo_path),
            patch("os.getcwd", return_value=str(repo_path)),
            patch(
                "src.nodes.integration_fixer.IntegrationFixerNodes.integration_fixer_node"
            ) as mock_fixer,
            patch(
                "src.nodes.sandbox_evaluator.SandboxEvaluatorNodes.sandbox_evaluate_node"
            ) as mock_sandbox,
            patch("src.services.git_ops.GitManager.merge_pr"),
        ):
            # Merge succeeds without conflict
            # Sandbox fails first, then passes
            mock_sandbox.side_effect = [{"status": "tdd_failed"}, {"status": "pass"}]
            # Fixer node acts
            mock_fixer.return_value = {"status": "fixed"}

            state = IntegrationState(branches_to_merge=["semantic-failure-feature"])

            try:
                result = await integration_graph.ainvoke(
                    state, config={"configurable": {"thread_id": "uat_semantic"}}
                )
            except Exception as e:
                return str(e), 0, False
            else:
                return result, mock_sandbox.call_count, mock_fixer.called

    result_3, sandbox_calls_3, fixer_called_3 = asyncio.run(run_scenario_3())

    if hasattr(mo, "ui"):
        mo.ui.table(
            [
                {
                    "Step": "Global Sandbox attempts",
                    "Expected": "2",
                    "Actual": f"{sandbox_calls_3}",
                },
                {
                    "Step": "Integration Fixer",
                    "Expected": "Called",
                    "Actual": f"Called: {fixer_called_3}",
                },
            ]
        )
    return fixer_called_3, result_3, run_scenario_3, sandbox_calls_3


if __name__ == "__main__":
    app.run()
