from typing import Any

from src.state import CycleState


class QaNodes:
    def __init__(self, jules: Any, git: Any, llm_reviewer: Any) -> None:
        self.jules = jules
        self.git = git
        self.llm_reviewer = llm_reviewer

    async def qa_session_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.qa_usecase import QaUseCase

        usecase = QaUseCase(self.jules, self.git, self.llm_reviewer)
        return dict(await usecase.execute_qa_session(state))

    async def qa_auditor_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.qa_usecase import QaUseCase

        usecase = QaUseCase(self.jules, self.git, self.llm_reviewer)
        return dict(await usecase.execute_qa_audit(state))
