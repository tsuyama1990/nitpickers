from typing import Any

from src.state import CycleState


class AuditorNodes:
    def __init__(self, mcp_client: Any = None, git: Any = None, llm_reviewer: Any = None) -> None:
        self.mcp_client = mcp_client
        self.git = git
        self.llm_reviewer = llm_reviewer

    async def auditor_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.auditor_usecase import AuditorUseCase, UATAuditorUseCase

        if getattr(state, "uat_execution_state", None):
            uat_usecase = UATAuditorUseCase(self.llm_reviewer)
            return dict(await uat_usecase.execute(state))

        usecase = AuditorUseCase(self.mcp_client, self.git, self.llm_reviewer)
        return dict(await usecase.execute(state))
