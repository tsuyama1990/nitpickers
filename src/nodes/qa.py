from typing import Any

from src.state import CycleState


class QaNodes:
    def __init__(self, mcp_client: Any = None, git: Any = None, llm_reviewer: Any = None) -> None:
        self.mcp_client = mcp_client
        self.git = git
        self.llm_reviewer = llm_reviewer

    async def qa_session_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.qa_usecase import QaUseCase

        usecase = QaUseCase(self.mcp_client, self.git, self.llm_reviewer)
        return dict(await usecase.execute_qa_session(state))

    async def qa_auditor_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.qa_usecase import QaUseCase

        usecase = QaUseCase(self.mcp_client, self.git, self.llm_reviewer)
        return dict(await usecase.execute_qa_audit(state))
