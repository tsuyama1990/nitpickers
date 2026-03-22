from collections.abc import Sequence
from typing import Any

from langchain_core.tools import BaseTool

from src.state import CycleState


class AuditorNodes:
    def __init__(self, jules: Any, git: Any, llm_reviewer: Any, e2b_tools: Sequence[BaseTool] | None = None) -> None:
        self.jules = jules
        self.git = git
        self.llm_reviewer = llm_reviewer
        self.e2b_tools = e2b_tools

    async def auditor_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.auditor_usecase import AuditorUseCase, UATAuditorUseCase

        if getattr(state, "uat_execution_state", None):
            uat_usecase = UATAuditorUseCase(self.llm_reviewer, e2b_tools=self.e2b_tools)
            return dict(await uat_usecase.execute(state))

        usecase = AuditorUseCase(self.jules, self.git, self.llm_reviewer, e2b_tools=self.e2b_tools)
        return dict(await usecase.execute(state))
