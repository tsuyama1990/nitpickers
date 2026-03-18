"""CLI module."""

import asyncio

import typer

from src.services.workflow import WorkflowService

app = typer.Typer()


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
    asyncio.run(
        service.run_cycle(
            cycle_id=cycle_id,
            resume=resume,
            auto=auto,
            start_iter=start_iter,
            project_session_id=session,
            parallel=parallel,
        )
    )
