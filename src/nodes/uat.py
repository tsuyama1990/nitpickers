from typing import Any

from src.state import CycleState


class UatNodes:
    def __init__(self, git: Any) -> None:
        self.git = git

    async def uat_evaluate_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.uat_usecase import UatUseCase

        usecase = UatUseCase(self.git)
        return dict(await usecase.execute(state))
