from typing import Any

from src.services.refactor_usecase import RefactorUsecase
from src.state import CycleState
from src.utils import logger


class GlobalRefactorNodes:
    """LangGraph node for executing global project refactoring."""

    def __init__(self, usecase: RefactorUsecase | None = None) -> None:
        self.usecase = usecase or RefactorUsecase()

    async def global_refactor_node(self, state: CycleState) -> dict[str, Any]:
        """
        Executes the global refactoring process using AST analysis and Jules.
        Updates the LangGraph state with the refactoring results.
        """
        logger.info("Executing Global Refactor Node...")

        try:
            result = await self.usecase.execute()

        except Exception as e:
            logger.error(f"Global Refactor Node encountered an error: {e}")
            return {"error": str(e)}
        else:
            if result.refactorings_applied:
                logger.info(
                    f"Refactorings successfully applied to {len(result.modified_files)} files."
                )
            else:
                logger.info("No global refactorings applied.")

            from src.enums import FlowStatus
            
            committee_update = state.committee.model_copy(update={"is_refactoring": True})
            return {
                "committee": committee_update,
                "status": FlowStatus.POST_AUDIT_REFACTOR,
            }
