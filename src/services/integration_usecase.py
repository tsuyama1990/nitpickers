from pathlib import Path

from src.config import settings
from src.domain_models.execution import ConflictRegistryItem
from src.services.conflict_manager import ConflictManager, ConflictMarkerRemainsError
from src.services.file_ops import FilePatcher
from src.services.llm_reviewer import LLMReviewer
from src.services.mcp_client_manager import McpClientManager
from src.state import IntegrationState
from src.utils import logger


class MaxRetriesExceededError(Exception):
    pass


class IntegrationUsecase:
    def __init__(
        self,
        mcp_client: McpClientManager | None = None,
        llm_reviewer: LLMReviewer | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.mcp_client = mcp_client or McpClientManager()
        self.llm_reviewer = llm_reviewer or LLMReviewer()
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
        # Master Integrator loop logic via MCP.
        # Now handles write tools.
        if not state.master_integrator_session_id:
            state.master_integrator_session_id = "master-integrator-session"
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
        # message history for this file context inside the session.
        # we can just use the global session, but for specific files, we might need a fresh context
        # or we just rely on the LLM's capacity if we maintain one list. For Master Integrator,
        # we'll maintain history just for this file's resolution to keep context window manageable.


        prompt = self.conflict_manager.build_conflict_package(item, repo_path)

        while item.resolution_attempts < max_retries:
            item.resolution_attempts += 1
            logger.info(
                f"Resolving {item.file_path} (Attempt {item.resolution_attempts}/{max_retries})"
            )

            # Use MCP GitHub read tools maybe, or just LLM
            async with self.mcp_client as _client:
                model = settings.reviewer.smart_model
                response_code = await self.llm_reviewer._ainvoke_with_tools(  # type: ignore
                    prompt=prompt, model=model, tools=[]
                )

            # Extract code block if any
            clean_code = self._extract_code_block(response_code)

            # Apply to file
            target_file = repo_path / item.file_path
            target_file.write_text(clean_code, encoding="utf-8")

            # Validate
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

        # If loop exits without returning, max retries reached.
        msg = f"Maximum conflict retries exceeded for {item.file_path}."
        raise MaxRetriesExceededError(msg)

    def _extract_code_block(self, response: str) -> str:
        """Extracts python/markdown code block if present."""
        import re

        match = re.search(r"```(?:\w+\n)?(.*?)```", response, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Fallback to returning the whole response if no markdown block
        return response.strip()
