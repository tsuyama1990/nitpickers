from typing import Any

from src.state import CycleState


class AuditorNodes:
    def __init__(self, jules: Any, git: Any, llm_reviewer: Any) -> None:
        self.jules = jules
        self.git = git
        self.llm_reviewer = llm_reviewer

    async def auditor_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.auditor_usecase import AuditorUseCase, UATAuditorUseCase

        if getattr(state, "uat_execution_state", None):
            uat_usecase = UATAuditorUseCase(self.llm_reviewer)
            return dict(await uat_usecase.execute(state))

        usecase = AuditorUseCase(self.jules, self.git, self.llm_reviewer)
        return dict(await usecase.execute(state))
