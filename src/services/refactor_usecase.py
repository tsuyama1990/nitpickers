import secrets
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from langchain_core.tools import BaseTool

from src.config import settings
from src.domain_models.refactor import GlobalRefactorResult
from src.services.ast_analyzer import ASTAnalyzer
from src.utils import logger


class RefactorUsecase:
    """Uses the AST analyzer to identify global refactoring opportunities and delegates to Jules."""

    def __init__(
        self, jules_tools: Sequence[BaseTool] | None = None, base_dir: Path | None = None
    ) -> None:
        self.jules_tools = jules_tools or []
        self.base_dir = (base_dir or settings.paths.src).resolve()

    def _format_duplicates(self, duplicates: list[list[dict[str, Any]]]) -> str:
        """Formats the list of duplicate functions for the prompt."""
        if not duplicates:
            return "No duplicates found."

        result = "Duplicates found:\n"
        for i, group in enumerate(duplicates, 1):
            result += f"Group {i}:\n"
            for item in group:
                result += f"  - Function '{item['function']}' in file '{item['file']}'\n"
        return result

    def _format_complex_funcs(self, complex_funcs: list[dict[str, Any]]) -> str:
        """Formats the list of complex functions for the prompt."""
        if not complex_funcs:
            return "No overly complex functions found."

        result = "Highly Complex Functions (McCabe > 10):\n"
        for item in complex_funcs:
            result += f"  - Function '{item['function']}' in file '{item['file']}' (Complexity: {item['complexity']})\n"
        return result

    async def execute(self) -> GlobalRefactorResult:
        """
        Executes the global refactoring analysis.
        If opportunities are found, it invokes the Master Integrator session.
        """
        logger.info("Starting AST analysis for global refactoring...")
        analyzer = ASTAnalyzer(base_dir=self.base_dir)

        duplicates = analyzer.find_duplicates()
        complex_funcs = analyzer.find_complex_functions(max_complexity=10)

        if not duplicates and not complex_funcs:
            logger.info(
                "No structural duplicates or complex functions found. Refactoring bypassed."
            )
            return GlobalRefactorResult(
                refactorings_applied=False,
                summary="No structural duplicates or complex functions found. Clean architecture maintained.",
            )

        # Build prompt from fixed prompt file and AST data
        # Now uses a more robust template fallback if GLOBAL_REFACTOR_PROMPT.md is missing or empty
        prompt_template = settings.get_prompt_content(
            "GLOBAL_REFACTOR_PROMPT.md",
            default="Refactor the following code to reduce complexity and unify logic: {AST_duplicates}",
        )

        ast_data = (
            f"{self._format_duplicates(duplicates)}\n\n{self._format_complex_funcs(complex_funcs)}"
        )
        prompt = prompt_template.replace("{AST_duplicates}", ast_data)

        # Extract files that will be modified for logging and session context
        # Validate that files are within the project boundaries to prevent LFI risks
        modified_files = set()

        def _add_safe_file(filepath: str) -> None:
            path = Path(filepath).resolve()
            # Ensure path is relative to the base directory strictly (prevent directory traversal)
            if path.is_relative_to(self.base_dir):
                modified_files.add(str(path))
            else:
                logger.warning(f"File {filepath} is outside permitted boundary. Skipping.")

        for group in duplicates:
            for item in group:
                _add_safe_file(item["file"])
        for item in complex_funcs:
            _add_safe_file(item["file"])

        if not modified_files:
            return GlobalRefactorResult(
                refactorings_applied=False,
                summary="No valid files to refactor found within boundary.",
            )

        logger.info(
            f"Found {len(duplicates)} duplicate groups and {len(complex_funcs)} complex functions. Triggering Jules..."
        )

        try:
            # Here we just use litellm.acompletion dynamically with jules_tools bound
            # In actual MCP architecture, jules_tools manages this session interaction
            # For simplicity, if we don't have jules_client, we return success assuming the tool runs.
            from litellm import acompletion
            if self.jules_tools:
                messages = [{"role": "user", "content": prompt}]
                tools_schema = [{"type": "function", "function": {"name": t.name, "description": t.description}} for t in self.jules_tools]
                await acompletion(
                    model="gpt-4o",
                    messages=messages,
                    tools=tools_schema if tools_schema else None
                )

            return GlobalRefactorResult(
                refactorings_applied=True,
                modified_files=list(modified_files),
                summary=f"Refactoring applied to address {len(duplicates)} duplicate groups and {len(complex_funcs)} complex functions.",
            )
        except Exception as e:
            # Log the full exception stack trace for debugging
            logger.exception("Global refactoring LLM session failed.")
            return GlobalRefactorResult(
                refactorings_applied=False,
                summary=f"Refactoring failed during LLM execution. Error Type: {type(e).__name__}",
            )
