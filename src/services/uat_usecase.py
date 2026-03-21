import re
import shlex
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

    ALLOWED_BINARIES: tuple[str, ...] = ("uv", "pytest", "python")
    DANGEROUS_SHELL_CHARS: tuple[str, ...] = (";", "&", "|", "$", "`", "\n", "<", ">")
    TEST_ID_PATTERN: re.Pattern[str] = re.compile(r"^[\w\.-]+$")
    PR_URL_PATTERN: re.Pattern[str] = re.compile(
        r"^https://github\.com/[\w.-]+/[\w.-]+/pull/\d+/?$"
    )

    def __init__(self, git_manager: GitManager) -> None:
        """
        Initializes the UatUseCase.

        Args:
            git_manager (GitManager): Instance for executing git operations like PR merges.
        """
        if not git_manager:
            msg = "GitManager must be injected into UatUseCase"
            raise ValueError(msg)
        self.git = git_manager

    def _scan_artifacts(self, stdout: str, stderr: str) -> list[MultiModalArtifact]:
        """
        Scans the local artifacts directory for multi-modal test artifacts (screenshots/traces).

        Args:
            stdout (str): Raw stdout from the test runner.
            stderr (str): Raw stderr from the test runner.

        Returns:
            list[MultiModalArtifact]: Validated list of multimodal artifacts.
        """
        artifacts_dir = settings.paths.artifacts_dir

        if not artifacts_dir.exists() or not artifacts_dir.is_dir():
            return []

        try:
            artifacts_dir = artifacts_dir.resolve(strict=True)
        except Exception as e:
            logger.error(f"Failed to resolve artifacts directory path: {e}")
            return []

        artifacts = []

        # Scan for multi-modal artifacts if directory exists
        if artifacts_dir.exists() and artifacts_dir.is_dir():
            # We expect PNG screenshots and ZIP traces named like {test_id}.png / {test_id}_trace.zip
            for img_path in artifacts_dir.glob("*.png"):
                base_name = img_path.stem
                # Validate test_id to prevent path traversal
                if not self.TEST_ID_PATTERN.match(base_name):
                    logger.warning(f"Invalid artifact filename: {base_name}")
                    continue

                zip_path = artifacts_dir / f"{base_name}_trace.zip"
                dom_path = artifacts_dir / f"{base_name}_dom.txt"

                if img_path.exists():
                    try:
                        artifact = MultiModalArtifact(
                            test_id=base_name,
                            screenshot_path=str(img_path),
                            trace_path=str(zip_path) if zip_path.exists() else None,
                            dom_snapshot_path=str(dom_path) if dom_path.exists() else None,
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
        """
        Executes the UAT Evaluation node.

        It deterministically executes Pytest with Playwright, evaluates the exit code,
        collects mult-modal artifacts on failure, or delegates to success handling.
        """
        logger.info("Running UAT Evaluation...")

        # Dynamic Execution using ProcessRunner
        runner = ProcessRunner()
        # Ensure we run the exact UAT tests folder with configurable browser args
        base_cmd = shlex.split(settings.uat.test_cmd)
        cmd = [*base_cmd, *settings.uat.playwright_args]

        # Security: whitelist allowed binaries to prevent command injection
        if not cmd or cmd[0] not in self.ALLOWED_BINARIES:
            msg = f"Unauthorized command binary: {cmd[0] if cmd else 'empty'}"
            raise ValueError(msg)

        # Security: prevent argument injection via shell metacharacters
        for arg in cmd:
            if any(char in arg for char in self.DANGEROUS_SHELL_CHARS):
                msg = f"Dangerous character detected in command argument: {arg}"
                raise ValueError(msg)

        # Ensure a clean state before executing dynamic UAT
        if getattr(settings.uat, "db_reset_cmd", None):
            logger.debug("Resetting sandbox database state...")
            await runner.run_command(shlex.split(str(settings.uat.db_reset_cmd)), check=True)

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
        """
        Handles the logic when UAT passes, including auto-merging the PR and
        calculating the correct state transition (Completed vs. Refactoring Phase).
        """
        # Auto-Merge Cycle PR
        pr_url = state.pr_url  # type: ignore

        if pr_url:
            if not settings.session.auto_merge_to_integration:
                logger.info(
                    "Auto-merge to integration branch is disabled by policy. Skipping merge."
                )
            else:
                # Security: Validate the PR URL structure strictly
                if not self.PR_URL_PATTERN.match(pr_url):
                    msg = f"Invalid PR URL format: {pr_url}"
                    logger.error(msg)
                    return {"status": FlowStatus.FAILED, "error": msg}

                parsed_url = urlparse(pr_url)
                pr_number = parsed_url.path.strip("/").split("/")[-1]

                try:
                    logger.info(f"Auto-merging Cycle PR #{pr_number}...")
                    await self.git.merge_pr(pr_number)  # type: ignore
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
