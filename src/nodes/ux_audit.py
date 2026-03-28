from typing import Any

from src.services.ux_auditor_usecase import UxAuditorUseCase
from src.state import CycleState


class UxAuditorNodes:
    async def ux_auditor_node(self, state: CycleState) -> dict[str, Any]:
        usecase = UxAuditorUseCase()
        return dict(await usecase.execute(state))
