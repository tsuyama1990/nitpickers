import asyncio
import sys
from pathlib import Path
from typing import Any

from langchain_core.runnables import RunnableConfig
from rich.console import Console
from rich.panel import Panel

from src.config import settings
from src.domain_models import CycleManifest
from src.domain_models.observability_config import ObservabilityConfig
from src.domain_models.tracing import TracingMetadata
from src.enums import FlowStatus, WorkPhase
from src.graph import GraphBuilder
from src.messages import SuccessMessages, ensure_api_key
from src.service_container import ServiceContainer
from src.services.async_dispatcher import AsyncDispatcher
from src.services.audit_orchestrator import AuditOrchestrator
from src.state import CycleState
from src.state_manager import StateManager
from src.utils import KeepAwake, logger

console = Console()


class WorkflowService:
    def __init__(self, services: ServiceContainer | None = None) -> None:
        self.services = services or ServiceContainer.default()

        self.builder = GraphBuilder(
            self.services,
            None,
            self.services.jules,
        )

    async def run_gen_cycles(
        self, cycles: int, project_session_id: str | None, auto_run: bool = False
    ) -> None:
        self.verify_environment_and_observability()
        with KeepAwake(reason="Generating Architecture and Cycles"):
            console.rule("[bold blue]Architect Phase: Generating Cycles[/bold blue]")

        ensure_api_key()
        graph = self.builder.build_architect_graph()

        initial_state = CycleState(cycle_id=settings.DUMMY_CYCLE_ID)
        initial_state.project_session_id = project_session_id
        initial_state.planned_cycle_count = cycles
        initial_state.requested_cycle_count = cycles

        try:
            thread_id = project_session_id or "architect-session"
            metadata = TracingMetadata(session_id=thread_id, execution_type="architect_phase")
            tracing_config = settings.tracing_service.get_run_config(metadata)

            config = RunnableConfig(
                configurable={"thread_id": thread_id},
                recursion_limit=settings.GRAPH_RECURSION_LIMIT,
                **tracing_config,  # type: ignore[typeddict-item]
            )
            final_state = await graph.ainvoke(initial_state, config)

            if final_state.get("error"):
                console.print(f"[red]Architect Phase Failed:[/red] {final_state['error']}")
                sys.exit(1)
            else:
                session_id_val = final_state["project_session_id"]
                integration_branch = final_state["integration_branch"]

                # In new strategy, integration_branch IS the feature branch
                feature_branch = integration_branch

                # Create Manifest with Cycles
                mgr = StateManager()
                manifest = mgr.create_manifest(
                    session_id_val,
                    feature_branch=feature_branch,
                    integration_branch=integration_branch,
                )
                manifest.cycles = [
                    CycleManifest(id=f"{i:02}", status="planned") for i in range(1, cycles + 1)
                ]
                mgr.save_manifest(manifest)

                console.print(
                    SuccessMessages.architect_complete(session_id_val, integration_branch)
                )

                if auto_run:
                    console.rule("[bold magenta]Auto-Running All Cycles[/bold magenta]")
                    # Chain execution: run all cycles with resume=False, auto=True (default), start_iter=1
                    await self._run_all_cycles(
                        resume=False,
                        auto=True,
                        start_iter=1,
                        project_session_id=session_id_val,
                    )

        except Exception as e:
            console.print(f"[bold red]Architect execution failed: {e}[/bold red]")
            logger.exception("Architect execution failed")

            # Rollback: Clean up any partial state
            if "session_id_val" in locals() and "mgr" in locals():
                try:
                    logger.warning(
                        f"Rolling back generated cycle plans for session {session_id_val}"
                    )
                    # A proper state cleanup would delete the generated state file or empty the cycle array
                    manifest_to_rollback = mgr.load_manifest()
                    if (
                        manifest_to_rollback
                        and manifest_to_rollback.project_session_id == session_id_val
                    ):
                        manifest_to_rollback.cycles = []
                        mgr.save_manifest(manifest_to_rollback)
                except Exception as rollback_err:
                    logger.error(f"Failed to rollback after error: {rollback_err}")

            sys.exit(1)
        finally:
            await self.builder.cleanup()

    async def run_cycle(
        self,
        cycle_id: str | None,
        resume: bool,
        auto: bool,
        start_iter: int,
        project_session_id: str | None,
        parallel: bool = False,
    ) -> None:
        self.verify_environment_and_observability()
        try:
            # Default to "all" behavior (resume pending) if no ID provided
            if cycle_id is None or cycle_id.lower() == "all":
                await self._run_all_cycles(resume, auto, start_iter, project_session_id, parallel)
                return

            await self._run_single_cycle(cycle_id, resume, auto, start_iter, project_session_id)
        finally:
            await self.builder.cleanup()

    def verify_environment_and_observability(self) -> None:
        """
        Validates observability parameters and checks explicitly/implicitly required
        dependencies based on environment variables and the local configuration.
        Implements the Phase 0 Gatekeeper pattern.
        """
        console.rule("[bold red]Phase 0: Environment & Observability Verification[/bold red]")
        try:
            # Pydantic schema enforcing invariants
            import os

            ObservabilityConfig(
                langchain_tracing_v2=os.getenv("LANGCHAIN_TRACING_V2", ""),
                langchain_api_key=os.getenv("LANGCHAIN_API_KEY", ""),
                langchain_project=os.getenv("LANGCHAIN_PROJECT", ""),
            )
        except Exception as e:
            console.print("[bold red]Observability check failed![/bold red]")
            console.print(f"[red]{e!s}[/red]")
            console.print(
                "[yellow]Please configure LANGCHAIN_TRACING_V2=true, LANGCHAIN_API_KEY, "
                "and LANGCHAIN_PROJECT in your .env file.[/yellow]"
            )
            import sys

            sys.exit(1)

        # Implicit dependency scan via SPEC documents
        try:
            import re

            docs_dir = settings.paths.documents_dir
            if not docs_dir.exists():
                docs_dir = Path.cwd() / "dev_documents"

            spec_path = docs_dir / "system_prompts" / "SPEC.md"
            if spec_path.exists():
                content = spec_path.read_text(encoding="utf-8")
                # Very basic scan for implicitly required secrets like DATABASE_URL, OPENAI_API_KEY
                for secret in settings.known_implicit_secrets:
                    if re.search(
                        r"\b" + re.escape(secret) + r"\b", content, re.IGNORECASE
                    ) and not os.getenv(secret):
                        console.print(f"[bold red]Implicit Dependency Missing: {secret}[/bold red]")
                        console.print(
                            f"[yellow]The specification file references '{secret}', "
                            f"but it was not found in the environment. Please configure it.[/yellow]"
                        )
                        import sys

                        sys.exit(1)
        except SystemExit:
            raise
        except Exception as e:
            logger.warning(f"Error scanning SPEC.md for implicit dependencies: {e}")

        console.print("[green]Environment & Observability verified successfully.[/green]")

    async def _run_all_cycles(
        self,
        resume: bool,
        auto: bool,
        start_iter: int,
        project_session_id: str | None,
        parallel: bool = False,
    ) -> None:
        mgr = StateManager()
        manifest = mgr.load_manifest()

        if manifest:
            # We construct instances of CycleManifest for all remaining ones to feed the dispatcher
            cycles_to_run = [c for c in manifest.cycles if c.status != "completed"]
        else:
            from src.domain_models.manifest import CycleManifest

            cycles_to_run = [CycleManifest(id=cid) for cid in settings.default_cycles]

        cycle_ids = [c.id for c in cycles_to_run]
        console.print(f"[bold cyan]Running Pending Cycles: {cycle_ids}[/bold cyan]")

        if not parallel:
            for idx, cid in enumerate(cycle_ids, 1):
                console.print(
                    f"[bold yellow]Starting Cycle {cid} ({idx}/{len(cycle_ids)})[/bold yellow]"
                )
                await self._run_single_cycle(str(cid), resume, auto, start_iter, project_session_id)
                console.print(
                    f"[bold green]Completed Cycle {cid} ({idx}/{len(cycle_ids)})[/bold green]"
                )
        else:
            dispatcher = AsyncDispatcher()
            batches = dispatcher.resolve_dag(cycles_to_run)
            console.print(
                f"[bold cyan]Parallel execution plan: {[[c.id for c in b] for b in batches]}[/bold cyan]"
            )

            for i, batch in enumerate(batches, 1):
                console.print(
                    f"[bold yellow]Starting Batch {i}/{len(batches)}: {[c.id for c in batch]}[/bold yellow]"
                )
                tasks = [
                    dispatcher.run_with_semaphore(
                        self._run_single_cycle(c.id, resume, auto, start_iter, project_session_id)
                    )
                    for c in batch
                ]
                await asyncio.gather(*tasks)
                console.print(f"[bold green]Completed Batch {i}/{len(batches)}[/bold green]")

        # After all cycles, run QA/Tutorial Generation
        await self.generate_tutorials(project_session_id)

        # Auto-finalize if requested
        if auto:
            await self.finalize_session(project_session_id)

    def _check_cycle_completion(self, cycle_id: str) -> bool:
        """Check if cycle is already completed."""
        mgr = StateManager()
        manifest = mgr.load_manifest()
        if manifest:
            cycle = next((c for c in manifest.cycles if c.id == cycle_id), None)
            if cycle and cycle.status == "completed":
                console.print(f"[yellow]Cycle {cycle_id} is already completed. Skipping.[/yellow]")
                return True
        return False

    async def _checkout_feature_branch(self, fb: str | None) -> None:
        """Check out the feature branch for the cycle."""
        if fb:
            from src.process_runner import ProcessRunner
            runner = ProcessRunner()
            logger.info(f"Checking out feature branch: {fb}")
            try:
                await runner.run_command(["git", "checkout", fb], check=True)
                await runner.run_command(["git", "pull"], check=False)
                logger.info(f"Successfully checked out feature branch: {fb}")
            except Exception as e:
                logger.warning(f"Could not checkout feature branch: {e}")
                logger.warning("Proceeding with current branch (may cause issues!)")
        else:
            logger.warning("No feature branch found in manifest. Using current branch.")

    async def _execute_cycle_graph(
        self,
        cycle_id: str,
        start_iter: int,
        resume: bool,
        pid: str | None,
        fb: str | None,
        ib: str | None,
        planned_count: int,
    ) -> None:
        """Execute the cycle graph."""
        graph = self.builder.build_coder_graph()
        state = CycleState(cycle_id=cycle_id)
        state.iteration_count = start_iter
        state.resume_mode = resume
        state.project_session_id = pid
        state.feature_branch = fb
        state.integration_branch = ib
        state.planned_cycle_count = planned_count

        thread_id = f"cycle-{cycle_id}-{state.project_session_id}"
        metadata = TracingMetadata(
            session_id=thread_id, execution_type="cycle_phase", git_branch=fb
        )
        tracing_config = settings.tracing_service.get_run_config(metadata)

        config = RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=settings.GRAPH_RECURSION_LIMIT,
            **tracing_config,  # type: ignore[typeddict-item]
        )
        final_state = await graph.ainvoke(state, config)

        if final_state.get("error"):
            console.print(f"[red]Cycle {cycle_id} Failed:[/red] {final_state['error']}")
            sys.exit(1)

        console.print(SuccessMessages.cycle_complete(cycle_id, f"{int(cycle_id) + 1:02}"))

    def _update_cycle_status(self, cycle_id: str) -> None:
        """Update cycle status to completed."""
        mgr = StateManager()
        if mgr.load_manifest():
            mgr.update_cycle_state(cycle_id, status="completed")

    async def _run_single_cycle(
        self,
        cycle_id: str,
        resume: bool,
        auto: bool,
        start_iter: int,
        project_session_id: str | None,
    ) -> None:
        if self._check_cycle_completion(cycle_id):
            return

        with KeepAwake(reason=f"Running Implementation Cycle {cycle_id}"):
            console.rule(f"[bold green]Coder Phase: Cycle {cycle_id}[/bold green]")

        ensure_api_key()

        try:
            if auto:
                settings.auto_approve = True

            mgr = StateManager()
            manifest = mgr.load_manifest()

            pid = project_session_id
            ib = None
            if manifest:
                pid = pid or manifest.project_session_id
                ib = manifest.integration_branch
            else:
                console.print("[red]No active session found. Run gen-cycles first.[/red]")
                sys.exit(1)

            fb = manifest.feature_branch if manifest else None
            await self._checkout_feature_branch(fb)

            planned_count = len(manifest.cycles) if manifest else 0
            await self._execute_cycle_graph(
                cycle_id, start_iter, resume, pid, fb, ib, planned_count
            )
            self._update_cycle_status(cycle_id)

        except Exception:
            console.print(f"[bold red]Cycle {cycle_id} execution failed.[/bold red]")
            logger.exception("Cycle execution failed")
            sys.exit(1)
        finally:
            await self.builder.cleanup()

    async def start_session(self, prompt: str, audit_mode: bool, max_retries: int) -> None:
        self.verify_environment_and_observability()
        console.rule("[bold magenta]Starting Jules Session[/bold magenta]")

        docs_dir = settings.paths.documents_dir
        spec_files = {
            str(docs_dir / f): (docs_dir / f).read_text(encoding="utf-8")
            for f in settings.architect_context_files
            if (docs_dir / f).exists()
        }

        if audit_mode:
            from src.services.mcp_client_manager import McpClientManager
            orch = AuditOrchestrator(McpClientManager(), self.builder.sandbox)
            try:
                result = await orch.run_interactive_session(
                    prompt=prompt,
                    spec_files=spec_files,
                    max_retries=max_retries,
                )
                if result and result.get("pr_url"):
                    console.print(
                        Panel(
                            f"Audit & Implementation Complete.\nPR: {result['pr_url']}",
                            style="bold green",
                        )
                    )
            except Exception:
                console.print("[bold red]Session Failed.[/bold red]")
                logger.exception("Session Failed")
                sys.exit(1)
        else:
            from src.services.mcp_client_manager import McpClientManager
            orch = AuditOrchestrator(McpClientManager(), self.builder.sandbox)
            try:
                result = await orch.run_interactive_session(
                    prompt=prompt,
                    spec_files=spec_files,
                    max_retries=0,
                )
                if result and result.get("pr_url"):
                    console.print(
                        Panel(
                            f"Implementation Sent.\nPR: {result['pr_url']}",
                            style="bold green",
                        )
                    )
            except Exception:
                console.print("[bold red]Session Failed.[/bold red]")
                logger.exception("Session Failed")
                sys.exit(1)

    async def generate_tutorials(self, project_session_id: str | None) -> None:
        """
        QA Phase: Generate and verify tutorials based on FINAL_UAT.md.
        """
        self.verify_environment_and_observability()
        console.rule("[bold cyan]QA Phase: Tutorial Generation[/bold cyan]")

        docs_dir = settings.paths.documents_dir
        qa_instruction_path = docs_dir / "system_prompts" / "QA_TUTORIAL_INSTRUCTION.md"

        if not qa_instruction_path.exists():
            console.print(
                "[yellow]Skipping Tutorial Generation: QA_TUTORIAL_INSTRUCTION.md not found.[/yellow]"
            )
            return

        if not qa_instruction_path.exists():
            console.print(
                "[yellow]Skipping Tutorial Generation: QA_TUTORIAL_INSTRUCTION.md not found.[/yellow]"
            )
            return

        # Build QA Graph
        graph = self.builder.build_qa_graph()

        # Initial State
        project_session_id = project_session_id or settings.current_session_id
        initial_state = CycleState(
            cycle_id="qa-tutorials",
            current_phase=WorkPhase.QA,
            status=FlowStatus.START,
        )
        initial_state.project_session_id = project_session_id

        thread_id = f"qa-{project_session_id}"
        metadata = TracingMetadata(session_id=thread_id, execution_type="qa_phase")
        tracing_config = settings.tracing_service.get_run_config(metadata)

        config = RunnableConfig(
            configurable={"thread_id": thread_id},
            recursion_limit=settings.GRAPH_RECURSION_LIMIT,
            **tracing_config,  # type: ignore[typeddict-item]
        )

        try:
            console.print("[cyan]Running QA Tutorial Generation Graph...[/cyan]")
            final_state = await graph.ainvoke(initial_state, config)

            audit_res = final_state.get("audit_result")
            if audit_res and getattr(audit_res, "is_approved", False):
                console.print(
                    Panel(
                        f"QA Tutorials Generated & Verified.\nPR: {final_state.get('pr_url')}",
                        style="bold green",
                    )
                )
            elif final_state.get("status") == "max_retries":
                console.print(
                    f"[bold yellow]QA Phase Warning: {final_state.get('error')}[/bold yellow]"
                )
                console.print("[yellow]Proceeding with best-effort results.[/yellow]")
            elif final_state.get("error"):
                console.print(f"[red]QA Phase Failed: {final_state['error']}[/red]")
            else:
                console.print("[yellow]QA Phase completed with uncertain status.[/yellow]")

        except Exception as e:
            console.print(f"[bold red]Tutorial Generation Failed:[/bold red] {e}")
            logger.exception("Tutorial Generation Failed")

    def _get_quality_gate_cmds(self) -> list[list[str]]:
        from src.config import settings

        cmds = []
        if settings.sandbox.lint_check_cmd:
            cmds.append(settings.sandbox.lint_check_cmd)
        if settings.sandbox.type_check_cmd:
            cmds.append(settings.sandbox.type_check_cmd)
        if settings.sandbox.test_cmd:
            cmds.append(settings.sandbox.test_cmd.split())

        if not cmds:
            cmds = [
                ["uv", "run", "ruff", "check", "."],
                ["uv", "run", "ruff", "format", "."],
                ["uv", "run", "mypy", "."],
                ["uv", "run", "pytest"],
            ]
        return cmds

    async def _handle_global_refactor_result(
        self, result: dict[str, Any], git: Any
    ) -> None:
        """Helper to handle the result of the global refactoring loop."""
        gr_res = result["global_refactor_result"]
        if not gr_res.refactorings_applied:
            return

        from src.process_runner import ProcessRunner
        from src.service_container import ServiceContainer

        container = ServiceContainer.default()
        runner = (
            container.resolve(ProcessRunner) if hasattr(container, "resolve") else ProcessRunner()
        )
        cmds = self._get_quality_gate_cmds()

        import shutil
        import tempfile
        from pathlib import Path

        # Execute quality gates in isolated temporary directories
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Copy current codebase to temp_dir to validate without affecting workspace yet
                # We want to run the tools in the temp dir
                temp_path = Path(temp_dir)

                # Exclude .git, .venv, etc when copying to save time and avoid issues
                def ignore_func(dir_path: str, contents: list[str]) -> list[str]:
                    return [c for c in contents if c in (".git", ".venv", "venv", "__pycache__")]

                shutil.copytree(Path.cwd(), temp_path / "workspace", ignore=ignore_func)
                workspace_dir = temp_path / "workspace"

                console.print(
                    "[cyan]Running final quality gates post-refactor in isolated sandbox...[/cyan]"
                )
                for cmd in cmds:
                    # This throws CalledProcessError if it fails
                    await runner.run_command(cmd, cwd=workspace_dir)

            # If we reached here, validations passed. Commit the changes in the actual workspace.
            status_output = await git.get_status()
            if status_output and status_output.strip():
                try:
                    await git.add_all()
                    await git.commit("Global refactoring applied.")
                    console.print("[green]Global refactoring successful and tests passed.[/green]")
                except Exception as commit_err:
                    console.print(
                        f"[bold red]Failed to commit global refactoring: {commit_err}[/bold red]"
                    )
                    await git.reset_hard()
        except Exception as e:
            console.print(
                f"[bold red]Quality gates failed after global refactoring: {e}[/bold red]"
            )
            console.print("[yellow]Reverting refactoring changes...[/yellow]")
            try:
                await git.reset_hard()
            except Exception as reset_err:
                console.print(f"[bold red]Failed to revert changes: {reset_err}[/bold red]")
            console.print(
                "[yellow]Refactoring changes reverted to maintain zero-trust validation.[/yellow]"
            )

    async def finalize_session(self, project_session_id: str | None) -> None:
        self.verify_environment_and_observability()
        console.rule("[bold cyan]Finalizing Development Session[/bold cyan]")
        ensure_api_key()

        mgr = StateManager()
        manifest = mgr.load_manifest()

        sid = project_session_id or (manifest.project_session_id if manifest else None)
        integration_branch = manifest.integration_branch if manifest else None

        if not sid or not integration_branch:
            console.print("[red]No active session found to finalize.[/red]")
            sys.exit(1)

        try:
            # Legacy finalization handling via Python is fully deprecated in CYCLE03.
            # Master Integrator commits and pushes remotely directly via MCP tools.
            # Thus, we simply note the finish.

            console.print(
                Panel("Session Finalized Successfully. Pull Requests tracked remotely.", style="bold green")
            )
            # Mark the session as finalized
            if manifest:
                manifest.is_session_finalized = True
                mgr.save_manifest(manifest)
            logger.info("Session finalized.")

        except Exception as e:
            logger.exception("Failed to finalize session.")
            console.print(f"[bold red]Failed to finalize session: {e}[/bold red]")
            sys.exit(1)

    async def _archive_and_reset_state(self) -> None:
        """
        Archives current session artifacts to dev_documents/system_prompts_phaseNN
        and resets the state for the next phase safely.
        """
        self.verify_environment_and_observability()
        from src.config import settings

        docs_dir = settings.paths.documents_dir
        if not docs_dir.exists():
            return

        next_phase_num = self._get_next_phase_num(docs_dir)
        dir_name = settings.ARCHIVE_DIR_TEMPLATE.format(phase_num=next_phase_num)
        phase_dir = docs_dir / dir_name
        console.print(f"\n[bold cyan]Archiving session artifacts to {phase_dir}...[/bold cyan]")

        try:
            await self._archive_files(docs_dir, phase_dir)
            self._reset_project_state(phase_dir)
            self._prepare_next_phase(docs_dir)
            await self._commit_archived_phase(next_phase_num)
        except Exception as e:
            logger.error(f"Failed during archive and reset state: {e}")
            # Consider rollback if needed, but this is best effort

        console.print("[green]Created fresh, empty ALL_SPEC.md for the next phase.[/green]")
        console.print(f"[green]Ready for Phase {next_phase_num + 1}![/green]")

    def _get_next_phase_num(self, docs_dir: Path) -> int:
        import contextlib

        existing_phases = [
            d
            for d in docs_dir.iterdir()
            if d.is_dir() and d.name.startswith("system_prompts_phase")
        ]
        nums = []
        for d in existing_phases:
            with contextlib.suppress(IndexError, ValueError):
                nums.append(int(d.name.split("_phase")[1]))
        return max(nums) + 1 if nums else 1

    async def _safe_move_item(self, src: Path, dest: Path) -> None:
        import shutil

        import anyio

        anyio_src = anyio.Path(src)
        anyio_dest = anyio.Path(dest)
        if not await anyio_src.exists():
            return
        await anyio_dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            from src.process_runner import ProcessRunner
            runner = ProcessRunner()
            await runner.run_command(["git", "mv", str(src), str(dest)], check=True)
        except Exception:
            try:
                await anyio_src.replace(dest)
            except OSError:
                shutil.move(str(src), str(dest))

    async def _archive_files(self, docs_dir: Path, phase_dir: Path) -> None:
        import anyio

        sys_prompts_dir = docs_dir / "system_prompts"
        if sys_prompts_dir.exists():
            await self._safe_move_item(sys_prompts_dir, phase_dir)
        else:
            await anyio.Path(phase_dir).mkdir(parents=True, exist_ok=True)

        await self._safe_move_item(docs_dir / "ALL_SPEC.md", phase_dir / "ALL_SPEC.md")
        await self._safe_move_item(
            docs_dir / "USER_TEST_SCENARIO.md", phase_dir / "USER_TEST_SCENARIO.md"
        )

        tutorials_dir = Path.cwd() / "tutorials"
        if tutorials_dir.exists():
            for item in tutorials_dir.iterdir():
                await self._safe_move_item(item, phase_dir / "tutorials" / item.name)
            await anyio.Path(tutorials_dir).mkdir(exist_ok=True)

        templates_dir = settings.paths.templates
        if templates_dir.exists():
            for cycle_dir in sorted(
                [d for d in templates_dir.iterdir() if d.is_dir() and d.name.startswith("CYCLE")]
            ):
                await self._safe_move_item(cycle_dir, phase_dir / "templates" / cycle_dir.name)

    def _reset_project_state(self, phase_dir: Path) -> None:
        import shutil

        state_mgr = StateManager()
        if state_mgr.STATE_FILE.exists():
            shutil.copy2(str(state_mgr.STATE_FILE), str(phase_dir / "project_state.json"))
            state_mgr.STATE_FILE.unlink()
            console.print("Project state reset (project_state.json archived and removed).")

    def _prepare_next_phase(self, docs_dir: Path) -> None:
        (docs_dir / "ALL_SPEC.md").touch()
        (docs_dir / "USER_TEST_SCENARIO.md").touch()
        (docs_dir / "system_prompts").mkdir(exist_ok=True)

    async def _commit_archived_phase(self, next_phase_num: int) -> None:
        from src.config import settings
        from src.process_runner import ProcessRunner

        msg = settings.ARCHIVE_COMMIT_MESSAGE.format(phase_num=next_phase_num)
        try:
            runner = ProcessRunner()
            await runner.run_command(["git", "add", "."], check=True)
            await runner.run_command(["git", "commit", "-m", msg], check=False)
        except Exception as e:
            logger.warning(f"Failed to commit archive: {e}")
