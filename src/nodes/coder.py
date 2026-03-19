from typing import Any

from src.state import CycleState


class CoderNodes:
    def __init__(self, jules: Any) -> None:
        self.jules = jules

    async def coder_session_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.coder_usecase import CoderUseCase

        usecase = CoderUseCase(self.jules)
        return dict(await usecase.execute(state))
