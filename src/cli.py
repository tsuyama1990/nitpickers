"""CLI module."""

import asyncio
import sys

import pydantic
import pydantic.fields
import typer

# HOTFIX: Bypass LangChain's broken pydantic.v1 imports with Pydantic 2.10+
sys.modules["pydantic.v1"] = pydantic
sys.modules["pydantic.v1.fields"] = pydantic.fields

from rich.console import Console  # noqa: E402

from src.config import settings  # noqa: E402
from src.services.project import ProjectManager  # noqa: E402
from src.services.workflow import WorkflowService  # noqa: E402

app = typer.Typer()
console = Console()


@app.command()
def init() -> None:
    """Initialize a new target project for Nitpick."""
    console.print("[bold blue]Initializing new Nitpick project...[/bold blue]")
    manager = ProjectManager()

    # The Docker container mounts the templates at /opt/nitpick/templates/
    templates_path = "/opt/nitpick/templates/"

    try:
        asyncio.run(manager.initialize_project(templates_path))

        console.print("[bold green]Initialization complete![/bold green]")
        console.print("\n[bold]Next Steps:[/bold]")
        console.print("1. Update [cyan]dev_documents/ALL_SPEC.md[/cyan] with your project specifications.")
        console.print("2. Update [cyan]dev_documents/USER_TEST_SCENARIO.md[/cyan] with your tutorial/UAT plan.")
        console.print("3. Ensure your required environment variables are listed in [cyan]dev_documents/required_envs.json[/cyan].")
        console.print("4. Add required environment variables to the root [cyan].env[/cyan] file.")
        console.print("5. Run [bold magenta]nitpick gen-cycles[/bold magenta] to architect your development plan.")

    except Exception as e:
        console.print(f"[bold red]Initialization failed:[/bold red] {e}")


@app.command()
def gen_cycles(
    cycles: int = typer.Option(
        settings.default_cycles_count, "--cycles", "-c", help="Number of cycles to generate"
    ),
    session: str | None = typer.Option(None, "--session", help="Session ID"),
) -> None:
    """Generate architecture and development cycles."""
    service = WorkflowService()
    asyncio.run(service.run_gen_cycles(cycles, project_session_id=session))


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


@app.command()
def run_pipeline(
    session: str | None = typer.Option(
        None, "--session", help="Session ID (if not using current state)"
    ),
) -> None:
    """Run the complete orchestrated 5-Phase pipeline."""
    service = WorkflowService()
    asyncio.run(service.run_full_pipeline(project_session_id=session))


@app.command()
def finalize_session(
    session: str | None = typer.Option(None, "--session", help="Session ID"),
) -> None:
    """Finalize the current working session."""
    service = WorkflowService()
    asyncio.run(service.finalize_session(project_session_id=session))
