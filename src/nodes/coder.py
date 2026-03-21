from collections.abc import Sequence
from typing import Any

from langchain_core.tools import BaseTool

from src.state import CycleState


class CoderNodes:
    def __init__(self, e2b_tools: Sequence[BaseTool] | None = None, github_read_tools: Sequence[BaseTool] | None = None) -> None:

        self.e2b_tools = e2b_tools
        self.github_read_tools = github_read_tools

    async def coder_session_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.coder_usecase import CoderUseCase

        usecase = CoderUseCase(None, e2b_tools=self.e2b_tools, github_read_tools=self.github_read_tools)
        return dict(await usecase.execute(state))
