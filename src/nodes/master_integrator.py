import re
from typing import Any

from src.config import settings
from src.services.llm_reviewer import LLMReviewer
from src.services.mcp_client_manager import McpClientManager
from src.state import CycleState
from src.utils import logger


class MasterIntegratorNodes:
    """Nodes for the Master Integrator concurrent execution flow via MCP."""

    def __init__(
        self,
        mcp_client: McpClientManager | None = None,
        llm_reviewer: LLMReviewer | None = None,
    ) -> None:
        self.mcp_client = mcp_client or McpClientManager()
        self.llm_reviewer = llm_reviewer or LLMReviewer()

    async def master_integrator_node(self, state: CycleState) -> dict[str, Any]:
        """
        Executes the master integrator node. Uses GitHub MCP Write tools to commit and PR.
        """
        logger.info("Executing Master Integrator Node with GitHub Write Tools...")

        try:
            # Build prompt based on code_changes or cycle state
            changes_summary = "\n".join([f"Modified {op.path}" for op in state.code_changes])
            if not changes_summary:
                changes_summary = "No files tracked in state.code_changes."

            prompt = (
                "You are the Master Integrator. Your job is to securely push the approved code changes "
                "to the repository using the provided GitHub tools.\n"
                f"Cycle ID: {state.cycle_id}\n"
                f"Changes to commit: \n{changes_summary}\n\n"
                "1. Use `push_commit` to push these changes to a new remote branch.\n"
                "2. Use `create_pull_request` to open a PR for the branch against main.\n"
                "Ensure the commit message and PR title are descriptive.\n"
                "Return the pull request URL and remote commit hash in your final response."
            )

            async with self.mcp_client as client:
                tools = await client.get_write_tools(server_name="github")
                model = settings.reviewer.smart_model

                # Here we use LLMReviewer (or directly litellm) to orchestrate tools
                response = await self.llm_reviewer._ainvoke_with_tools(  # type: ignore
                    prompt=prompt, model=model, tools=tools
                )

        except Exception as e:
            logger.error(f"Master Integrator node encountered an error: {e}")
            return {"error": str(e)}
        else:
            # Parse response for PR URL or remote hash if the LLM output them
            pr_url = None
            remote_commit_hash = None

            # Simple extraction from text
            pr_match = re.search(r"https://github\.com/[\w.-]+/[\w.-]+/pull/\d+", response)
            if pr_match:
                pr_url = pr_match.group(0)

            hash_match = re.search(r"commit hash:? ([a-f0-9]{40})", response, re.IGNORECASE)
            if hash_match:
                remote_commit_hash = hash_match.group(1)

            return {
                "pull_request_url": pr_url,
                "remote_commit_hash": remote_commit_hash,
            }
