import logging
from typing import Any

import marimo

logger = logging.getLogger(__name__)

__generated_with = "0.10.19"
app = marimo.App()


@app.cell
def cell_1(mo: Any) -> Any:
    mo.md(
        r"""
        # CYCLE 08 UAT Verification
        This script verifies the behavior defined in `CYCLE08/UAT.md`.
        """
    )


@app.cell
def cell_2() -> Any:
    import tempfile
    from pathlib import Path
    from unittest.mock import AsyncMock, patch

    from src.services.jules_client import JulesClient

    from src.nodes.global_refactor import GlobalRefactorNodes
    from src.services.refactor_usecase import RefactorUsecase
    from src.state import CycleState

    # Scenario ID 08-01: Successful Global Refactoring
    async def verify_successful_refactoring() -> bool:
        logger.info("Running verify_successful_refactoring...")
        jules_client = AsyncMock(spec=JulesClient)
        jules_client.run_session.return_value = {"pr_url": "mock_pr_url"}

        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)

            usecase = RefactorUsecase(jules_client=jules_client, base_dir=base_dir)  # type: ignore
            nodes = GlobalRefactorNodes(usecase=usecase)
            state = CycleState(cycle_id="08")
            state.project_session_id = "session-1"

            with patch("src.services.refactor_usecase.ASTAnalyzer") as mock_analyzer:
                instance = mock_analyzer.return_value
                instance.find_duplicates.return_value = [
                    [{"file": "a.py", "function": "func1"}, {"file": "b.py", "function": "func1"}]
                ]
                instance.find_complex_functions.return_value = []

                new_state = await nodes.global_refactor_node(state)

                assert "global_refactor_result" in new_state
                assert new_state["global_refactor_result"].refactorings_applied is True
                jules_client.run_session.assert_called_once()
        logger.info("verify_successful_refactoring passed")
        return True

    # Scenario ID 08-03: Unmodified Clean Architecture
    async def verify_clean_architecture() -> bool:
        logger.info("Running verify_clean_architecture...")
        jules_client = AsyncMock(spec=JulesClient)

        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)

            usecase = RefactorUsecase(jules_client=jules_client, base_dir=base_dir)  # type: ignore
            nodes = GlobalRefactorNodes(usecase=usecase)
            state = CycleState(cycle_id="08")
            state.project_session_id = "session-1"

            with patch("src.services.refactor_usecase.ASTAnalyzer") as mock_analyzer:
                instance = mock_analyzer.return_value
                instance.find_duplicates.return_value = []
                instance.find_complex_functions.return_value = []

                new_state = await nodes.global_refactor_node(state)

                assert "global_refactor_result" in new_state
                assert new_state["global_refactor_result"].refactorings_applied is False
                jules_client.run_session.assert_not_called()
        logger.info("verify_clean_architecture passed")
        return True

    return (verify_successful_refactoring, verify_clean_architecture)


@app.cell
def cell_3(verify_clean_architecture: Any, verify_successful_refactoring: Any) -> Any:
    import asyncio

    async def run_all() -> None:
        await verify_successful_refactoring()
        await verify_clean_architecture()
        logger.info("All UATs passed!")

    loop = asyncio.get_event_loop()
    if loop.is_running():
        import nest_asyncio

        nest_asyncio.apply()
        asyncio.run(run_all())
    else:
        loop.run_until_complete(run_all())


if __name__ == "__main__":
    app.run()
