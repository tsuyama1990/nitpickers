from typing import Any

from src.state import CycleState


class CommitteeNodes:
    async def committee_manager_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.committee_usecase import CommitteeUseCase

        usecase = CommitteeUseCase()
        return dict(await usecase.execute(state))
