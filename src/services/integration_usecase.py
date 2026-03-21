from pathlib import Path

from collections.abc import Sequence
from typing import Any

from langchain_core.tools import BaseTool
import litellm

from src.config import settings
from src.domain_models.execution import ConflictRegistryItem
from src.services.conflict_manager import ConflictManager, ConflictMarkerRemainsError
from src.services.file_ops import FilePatcher
from src.state import IntegrationState
from src.utils import logger


class MaxRetriesExceededError(Exception):
    pass


class IntegrationUsecase:
    def __init__(
        self,
        github_write_tools: Sequence[BaseTool] | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.github_write_tools = github_write_tools or []
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
        Sends unresolved conflicts sequentially to litellm agents using MCP tools.
        Validates the output. If markers remain, retries up to max limits.
        """
        # We don't need a dedicated session ID from Jules anymore since we use litellm stateless interactions
        if not state.master_integrator_session_id:
            state.master_integrator_session_id = "master-integrator-session-mcp"

        for i, item in enumerate(state.unresolved_conflicts):
            if item.resolved:
                continue

            try:
                await self._resolve_single_file(item, repo_path)
            except Exception as e:
                logger.error(f"Failed to resolve file {item.file_path}: {e}")
                msg = f"Failed to resolve {item.file_path}: {e}"
                raise MaxRetriesExceededError(msg) from e

            state.unresolved_conflicts[i] = item

        # Finally, orchestrate MCP commit & PR creation
        await self._create_pull_request()

        return state

    async def _create_pull_request(self) -> None:
        """Uses litellm to instruct the agent to push commits and create a PR via github_write_tools."""
        logger.info("Executing GitHub PR generation via MCP...")

        if not self.github_write_tools:
            logger.warning("No github write tools provided, skipping PR generation.")
            return

        instruction = settings.get_prompt_content("MASTER_INTEGRATOR_INSTRUCTION.md")
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": instruction},
            {
                "role": "user",
                "content": "All conflicts have been resolved locally. Please push the commit and create a pull request.",
            },
        ]

        tools_schema = []
        for tool in self.github_write_tools:
            parameters = {"type": "object", "properties": {}}
            if hasattr(tool, "args_schema") and hasattr(tool.args_schema, "model_json_schema"):
                parameters = tool.args_schema.model_json_schema()  # type: ignore[union-attr]

            tools_schema.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": parameters,
                }
            })

        for _ in range(3):  # Tool execution loop
            try:
                response = await litellm.acompletion(
                    model=settings.reviewer.smart_model,
                    messages=messages,
                    tools=tools_schema if tools_schema else None,
                    temperature=settings.reviewer.master_integrator_temperature,
                )

                choice = response.choices[0]
                message = choice.message
                messages.append(message.to_dict())

                if message.tool_calls:
                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = tool_call.function.arguments

                        tool_instance = next(
                            (t for t in self.github_write_tools if t.name == func_name), None
                        )

                        if tool_instance:
                            import json
                            args_dict = json.loads(func_args)
                            tool_result = await tool_instance.ainvoke(args_dict)
                            messages.append({
                                "role": "tool",
                                "name": func_name,
                                "tool_call_id": tool_call.id,
                                "content": str(tool_result),
                            })
                        else:
                            messages.append({
                                "role": "tool",
                                "name": func_name,
                                "tool_call_id": tool_call.id,
                                "content": f"Error: Tool {func_name} not found.",
                            })
                else:
                    # Agent finished successfully
                    break
            except Exception as e:
                logger.error(f"Error communicating with LLM during PR creation: {e}")
                break

    async def _resolve_single_file(
        self, item: ConflictRegistryItem, repo_path: Path
    ) -> None:
        max_retries = self.max_retries
        messages: list[dict[str, Any]] = []

        system_instruction = settings.get_prompt_content("MASTER_INTEGRATOR_INSTRUCTION.md")
        messages.append({"role": "system", "content": system_instruction})

        prompt = self.conflict_manager.build_conflict_package(item, repo_path)
        messages.append({"role": "user", "content": prompt})

        while item.resolution_attempts < max_retries:
            item.resolution_attempts += 1
            logger.info(
                f"Resolving {item.file_path} (Attempt {item.resolution_attempts}/{max_retries})"
            )

            # Send to litellm
            try:
                response = await litellm.acompletion(
                    model=settings.reviewer.smart_model,
                    messages=messages,
                    temperature=settings.reviewer.master_integrator_temperature,
                )
            except Exception as e:
                logger.error(f"Error communicating with LLM: {e}")
                raise

            choice = response.choices[0]
            message_content = choice.message.content or ""
            messages.append({"role": "assistant", "content": message_content})

            # Extract code block if any
            clean_code = self._extract_code_block(message_content)

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
                messages.append({"role": "user", "content": prompt})

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
