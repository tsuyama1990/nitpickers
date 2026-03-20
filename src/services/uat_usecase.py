from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from src.config import settings
from src.domain_models.multimodal_artifact_schema import MultiModalArtifact
from src.domain_models.uat_execution_state import UatExecutionState
from src.enums import FlowStatus, WorkPhase
from src.process_runner import ProcessRunner
from src.services.git_ops import GitManager
from src.state import CycleState
from src.utils import logger


class UatUseCase:
    """
    Encapsulates the logic for UAT Evaluation, Auto-Merge, and Refactoring Transition.
    """

    def __init__(self, git_manager: GitManager) -> None:
        if not git_manager:
            msg = "GitManager must be injected into UatUseCase"
            raise ValueError(msg)
        self.git = git_manager

    def _scan_artifacts(self, stdout: str, stderr: str) -> list[MultiModalArtifact]:
        """Scans the artifacts directory for multi-modal artifacts."""
        artifacts_dir = settings.paths.artifacts_dir

        if not artifacts_dir.exists() or artifacts_dir.is_symlink() or not artifacts_dir.is_dir():
            return []

        try:
            artifacts_dir = artifacts_dir.resolve(strict=True)
        except Exception as e:
            logger.error(f"Failed to resolve artifacts directory path: {e}")
            return []

        # Security: Prevent path traversal
        if not artifacts_dir.is_relative_to(Path.cwd()):
            logger.error(f"Invalid artifacts directory path: {artifacts_dir}")
            return []

        artifacts = []

        # Scan for multi-modal artifacts if directory exists
        if artifacts_dir.exists() and artifacts_dir.is_dir():
            # We expect PNG screenshots and ZIP traces named like {test_id}.png / {test_id}_trace.zip
            for img_path in artifacts_dir.glob("*.png"):
                base_name = img_path.stem
                zip_path = artifacts_dir / f"{base_name}_trace.zip"

                if img_path.exists() and zip_path.exists():
                    try:
                        artifact = MultiModalArtifact(
                            test_id=base_name,
                            screenshot_path=str(img_path),
                            trace_path=str(zip_path),
                            console_logs=[],
                            traceback=(
                                stderr[-settings.uat.traceback_limit :]
                                if stderr
                                else stdout[-settings.uat.traceback_limit :]
                            ),
                        )
                        artifacts.append(artifact)
                    except Exception as e:
                        logger.warning(f"Failed to parse artifact {base_name}: {e}")
        return artifacts

    async def execute(self, state: CycleState) -> dict[str, Any]:
        """Node for UAT Evaluation, Auto-Merge, and Refactoring Transition."""
        logger.info("Running UAT Evaluation...")

        import shlex

        # Dynamic Execution using ProcessRunner
        runner = ProcessRunner()
        # Ensure we run the exact UAT tests folder with configurable browser args
        base_cmd = shlex.split(settings.uat.test_cmd)
        cmd = [*base_cmd, *settings.uat.playwright_args]
        logger.debug(f"Executing: {' '.join(cmd)}")
        stdout, stderr, exit_code, _timeout_occurred = await runner.run_command(cmd, check=False)

        if exit_code != 0:
            logger.error(f"UAT Execution Failed with exit code {exit_code}.")
            artifacts = self._scan_artifacts(stdout, stderr)

            uat_state = UatExecutionState(
                exit_code=exit_code, stdout=stdout, stderr=stderr, artifacts=artifacts
            )
            return {
                "status": FlowStatus.UAT_FAILED,
                "uat_execution_state": uat_state,
                "error": "UAT dynamically failed",
            }

        logger.info("UAT Execution Passed.")
        return await self._handle_success(state)

    async def _handle_success(self, state: CycleState) -> dict[str, Any]:
        """Handles the logic when UAT passes, including auto-merging and phase transition."""
        # Auto-Merge Cycle PR
        pr_url = state.pr_url
        if pr_url:
            try:
                parsed_url = urlparse(pr_url)
                pr_number = parsed_url.path.strip("/").split("/")[-1]
                logger.info(f"Auto-merging Cycle PR #{pr_number}...")
                await self.git.merge_pr(pr_number)
                logger.info("Cycle PR merged successfully!")
            except Exception as e:
                logger.error(f"Failed to auto-merge Cycle PR: {e}")
                return {"status": FlowStatus.FAILED, "error": str(e)}

        # Refactoring Phase Transition Logic
        current_phase = state.current_phase

        # Determine if this is the last cycle
        try:
            cycle_id_int = int(state.cycle_id)
        except (ValueError, TypeError):
            cycle_id_int = 0

        planned_count = state.planned_cycle_count or 0
        is_last_cycle = cycle_id_int >= planned_count

        if current_phase != WorkPhase.REFACTORING:
            if is_last_cycle:
                logger.info("All cycles completed. Transitioning to Final Refactoring Phase...")
                # Clear audit results and reset counters for the refactoring loop
                return {
                    "current_phase": WorkPhase.REFACTORING,
                    "status": FlowStatus.START_REFACTOR,
                    "iteration_count": 0,
                    "current_auditor_index": 1,
                    "current_auditor_review_count": 1,
                    "audit_result": None,
                    "audit_pass_count": 0,
                    "audit_retries": 0,
                    "final_fix": True,  # Final Refactor phase bypasses committee audit to be "Final"
                    "last_feedback_time": 0,
                    "pr_url": None,
                }
            logger.info(f"Cycle {state.cycle_id} of {planned_count} completed.")
            return {"status": FlowStatus.COMPLETED}

        # If we were already in refactoring, we are done
        logger.info("Refactoring Phase Completed.")
        return {"status": FlowStatus.COMPLETED}
