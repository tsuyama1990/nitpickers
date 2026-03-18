from pathlib import Path
from typing import Any

from src.config import settings
from src.domain_models.refactor import GlobalRefactorResult
from src.services.ast_analyzer import ASTAnalyzer
from src.services.jules_client import JulesClient
from src.utils import logger


class RefactorUsecase:
    """Uses the AST analyzer to identify global refactoring opportunities and delegates to Jules."""

    def __init__(self, jules_client: JulesClient | None = None, base_dir: Path | None = None) -> None:
        self.jules_client = jules_client or JulesClient()
        self.base_dir = base_dir or settings.paths.src

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
            logger.info("No structural duplicates or complex functions found. Refactoring bypassed.")
            return GlobalRefactorResult(
                refactorings_applied=False,
                summary="No structural duplicates or complex functions found. Clean architecture maintained.",
            )

        # Build prompt from fixed prompt file and AST data
        prompt_template = settings.get_prompt_content(
            "GLOBAL_REFACTOR_PROMPT.md",
            default="Analyze the complete project context. Unify duplicated logic across the following modules: {AST_duplicates}. Ensure consistent error handling and typing. Ensure maximum McCabe complexity is strictly under 10. Do not break existing tests.",
        )

        ast_data = f"{self._format_duplicates(duplicates)}\n\n{self._format_complex_funcs(complex_funcs)}"
        prompt = prompt_template.replace("{AST_duplicates}", ast_data)

        # Extract files that will be modified for logging and session context
        modified_files = set()
        for group in duplicates:
            for item in group:
                modified_files.add(item["file"])
        for item in complex_funcs:
            modified_files.add(item["file"])

        logger.info(f"Found {len(duplicates)} duplicate groups and {len(complex_funcs)} complex functions. Triggering Jules...")

        # Invoke the Master Integrator Session
        session_id = f"master-integrator-{settings.current_session_id}"

        try:
            # We assume the Master Integrator session handles modifications based on the prompt.
            # Using run_session directly which acts on the codebase.
            await self.jules_client.run_session(
                session_id=session_id,
                prompt=prompt,
                files=list(modified_files)
            )

            return GlobalRefactorResult(
                refactorings_applied=True,
                modified_files=list(modified_files),
                summary=f"Refactoring applied to address {len(duplicates)} duplicate groups and {len(complex_funcs)} complex functions.",
            )
        except Exception as e:
            logger.error(f"Global refactoring session failed: {e}")
            return GlobalRefactorResult(
                refactorings_applied=False,
                summary=f"Refactoring failed during LLM execution: {e!s}",
            )
