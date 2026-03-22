from collections.abc import Sequence
from typing import Any

from langchain_core.tools import BaseTool

from src.state import CycleState


class QaNodes:
    def __init__(self, e2b_tools: Sequence[BaseTool] | None = None) -> None:



        self.e2b_tools = e2b_tools

    async def qa_session_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.qa_usecase import QaUseCase
        from src.services.llm_reviewer import LLMReviewer

        usecase = QaUseCase(None, None, LLMReviewer(), e2b_tools=self.e2b_tools)
        return dict(await usecase.execute_qa_session(state))

    async def qa_auditor_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.qa_usecase import QaUseCase
        from src.services.llm_reviewer import LLMReviewer

        usecase = QaUseCase(None, None, LLMReviewer(), e2b_tools=self.e2b_tools)
        return dict(await usecase.execute_qa_audit(state))
