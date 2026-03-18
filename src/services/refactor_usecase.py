import secrets
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
            logger.info("No structural duplicates or complex functions found. Refactoring bypassed.")
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

        ast_data = f"{self._format_duplicates(duplicates)}\n\n{self._format_complex_funcs(complex_funcs)}"
        prompt = prompt_template.replace("{AST_duplicates}", ast_data)

        # Extract files that will be modified for logging and session context
        # Validate that files are within the project boundaries to prevent LFI risks
        modified_files = set()

        def _add_safe_file(filepath: str) -> None:
            path = Path(filepath).resolve()
            # Ensure path is relative to the base directory (prevent directory traversal)
            try:
                path.relative_to(self.base_dir.parent)
                modified_files.add(str(path))
            except ValueError:
                logger.warning(f"File {filepath} is outside permitted boundary. Skipping.")

        for group in duplicates:
            for item in group:
                _add_safe_file(item["file"])
        for item in complex_funcs:
            _add_safe_file(item["file"])

        if not modified_files:
            return GlobalRefactorResult(
                refactorings_applied=False,
                summary="No valid files to refactor found within boundary."
            )

        logger.info(f"Found {len(duplicates)} duplicate groups and {len(complex_funcs)} complex functions. Triggering Jules...")

        # Securely generate Session ID to prevent session fixation attacks
        secure_token = secrets.token_hex(8)
        session_id = f"master-integrator-{settings.current_session_id}-{secure_token}"

        try:
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
            # Generic error to prevent sensitive stacktrace leakage
            error_type = type(e).__name__
            logger.error(f"Global refactoring LLM session failed ({error_type}): Review logs for details.")
            return GlobalRefactorResult(
                refactorings_applied=False,
                summary=f"Refactoring failed during LLM execution. Error Type: {error_type}",
            )
