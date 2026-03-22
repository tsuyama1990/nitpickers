from collections.abc import Sequence
from typing import Any

from langchain_core.tools import BaseTool

from src.state import CycleState


class UatNodes:
    def __init__(self, e2b_tools: Sequence[BaseTool] | None = None) -> None:

        self.e2b_tools = e2b_tools

    async def uat_evaluate_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.uat_usecase import UatUseCase

        usecase = UatUseCase(None, e2b_tools=self.e2b_tools)
        return dict(await usecase.execute(state))
