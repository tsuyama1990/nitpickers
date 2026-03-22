from pathlib import Path

from src.domain_models.execution import ConflictRegistryItem, ConflictResolutionSchema
from src.services.conflict_manager import ConflictManager, ConflictMarkerRemainsError
from src.services.file_ops import FilePatcher
from src.services.jules_client import JulesClient
from src.state import IntegrationState
from src.utils import logger


class MaxRetriesExceededError(Exception):
    pass


class IntegrationUsecase:
    def __init__(
        self, jules_client: JulesClient | None = None, max_retries: int | None = None
    ) -> None:
        self.jules = jules_client or JulesClient()
        self.conflict_manager = ConflictManager()
        self.file_ops = FilePatcher()

        if max_retries is not None:
            self.max_retries = max_retries
        else:
            try:
                from src.config import settings

                self.max_retries = settings.max_audit_retries + 1
            except ImportError:
                self.max_retries = 3

    async def run_integration_loop(
        self, state: IntegrationState, repo_path: Path
    ) -> IntegrationState:
        """
        Runs the Master Integrator loop.
        Sends unresolved conflicts sequentially to the stateful Jules session.
        Validates the output. If markers remain, retries up to max limits.
        """
        # Ensure session exists
        if not state.master_integrator_session_id:
            state.master_integrator_session_id = self.jules.create_master_integrator_session()
            logger.info(f"Created Master Integrator Session: {state.master_integrator_session_id}")

        for i, item in enumerate(state.unresolved_conflicts):
            if item.resolved:
                continue

            try:
                await self._resolve_single_file(state.master_integrator_session_id, item, repo_path)
            except Exception as e:
                logger.error(f"Failed to resolve file {item.file_path}: {e}")
                msg = f"Failed to resolve {item.file_path}: {e}"
                raise MaxRetriesExceededError(msg) from e

            state.unresolved_conflicts[i] = item

        return state

    async def _resolve_single_file(
        self, session_id: str, item: ConflictRegistryItem, repo_path: Path
    ) -> None:
        max_retries = self.max_retries
        message_history: list[dict[str, str]] = []

        prompt = await self.conflict_manager.build_conflict_package(item, repo_path)

        # Enforce JSON output for validation against schema
        prompt += (
            "\n\nReturn the exact JSON object strictly matching this schema:\n"
            f"{ConflictResolutionSchema.model_json_schema()}"
        )

        from src.config import settings

        model = settings.reviewer.smart_model

        while item.resolution_attempts < max_retries:
            item.resolution_attempts += 1
            logger.info(
                f"Resolving {item.file_path} (Attempt {item.resolution_attempts}/{max_retries})"
            )

            response_code = await self.jules.send_message_to_session(
                session_id, prompt, message_history, model=model
            )

            clean_code = None
            try:
                # Clean up markdown JSON blocks if present
                import re

                json_str = response_code
                match = re.search(r"```(?:json)?\n(.*?)```", response_code, re.DOTALL)
                if match:
                    json_str = match.group(1).strip()

                resolution = ConflictResolutionSchema.model_validate_json(json_str)
                clean_code = resolution.resolved_code
            except Exception as e:
                logger.warning(f"Failed to parse or validate schema: {e}")
                prompt = (
                    "Your response did not match the strictly required JSON schema or was malformed.\n"
                    f"Error: {e}\n"
                    "Ensure your entire response is a single valid JSON object strictly matching:\n"
                    f"{ConflictResolutionSchema.model_json_schema()}"
                )
                continue

            target_file = repo_path / item.file_path
            target_file.write_text(clean_code, encoding="utf-8")

            try:
                if self.conflict_manager.validate_resolution(target_file):
                    logger.info(f"Successfully resolved {item.file_path}.")
                    item.resolved = True
                    return
            except ConflictMarkerRemainsError as e:
                logger.warning(f"Resolution failed for {item.file_path}: {e}")
                prompt = (
                    "Your resolution failed. Conflict markers `<<<<<<<` still exist. "
                    "Fix it. Ensure the output does not contain standard Git conflict markers."
                )

        msg = f"Maximum conflict retries exceeded for {item.file_path}."
        raise MaxRetriesExceededError(msg)
