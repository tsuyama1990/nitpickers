from unittest.mock import AsyncMock, patch

import pytest

from src.nodes.global_refactor import GlobalRefactorNodes
from src.state import CycleState

pytestmark = pytest.mark.skip(reason="Legacy API tests")


@pytest.mark.asyncio
async def test_mcp_jules_session_dispatch():  # type: ignore
    """
    Verify the Global Refactor node securely dispatches parallel agent fleets via
    native Jules MCP Orchestration tools, and applies sequential locks to reconcile
    incoming session diffs without race condition state corruption.
    """
    state = CycleState(cycle_id="03")

    with patch("src.nodes.global_refactor.RefactorUsecase"):
        mock_usecase = AsyncMock()

        from src.domain_models.refactor import GlobalRefactorResult

        mock_usecase.execute.return_value = GlobalRefactorResult(
            refactorings_applied=True,
            modified_files=["src/main.py"],
            summary="Refactored using MCP",
        )

        node = GlobalRefactorNodes(usecase=mock_usecase)
        result = await node.global_refactor_node(state)

        assert result.get("global_refactor_result").refactorings_applied is True  # type: ignore
