"""CLI module."""

import asyncio

import typer

from src.mcp_router.manager import McpClientManager
from src.services.workflow import WorkflowService

app = typer.Typer()


@app.command()
def gen_cycles(
    cycles: int = typer.Option(5, "--cycles", "-c", help="Number of cycles to generate"),
    session: str | None = typer.Option(None, "--session", help="Session ID"),
) -> None:
    """Generate architecture and development cycles."""

    async def _run() -> None:
        service = WorkflowService()
        await service.run_gen_cycles(cycles, project_session_id=session)

    asyncio.run(_run())


@app.command()
def run_cycle(
    cycle_id: str = typer.Option("all", "--id", "-i", help="Cycle ID to run (e.g., '01') or 'all'"),
    resume: bool = typer.Option(False, "--resume", "-r", help="Resume from last failed node"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Auto-approve AI decisions"),
    start_iter: int = typer.Option(1, "--start-iter", "-s", help="Starting iteration count"),
    session: str = typer.Option(None, "--session", help="Session ID (if not using current state)"),
    parallel: bool = typer.Option(
        False, "--parallel", "-p", help="Run multiple cycles concurrently based on DAG"
    ),
) -> None:
    """Run one or all development cycles."""
    service = WorkflowService()

    # Pre-flight environment check
    service.verify_environment_and_observability()

    async def _run() -> None:
        manager = McpClientManager()
        async with manager.get_client() as client:
            tools = await client.get_tools()
            await service.run_cycle(
                cycle_id=cycle_id,
                resume=resume,
                auto=auto,
                start_iter=start_iter,
                project_session_id=session,
                parallel=parallel,
                e2b_tools=tools,
            )

    asyncio.run(_run())


@app.command()
def finalize_session(
    session: str | None = typer.Option(None, "--session", help="Session ID"),
) -> None:
    """Finalize the current working session."""
    async def _run() -> None:
        service = WorkflowService()
        await service.finalize_session(project_session_id=session)

    asyncio.run(_run())
