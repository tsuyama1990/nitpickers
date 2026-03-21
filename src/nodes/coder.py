from typing import Any

from src.state import CycleState


class CoderNodes:
    def __init__(self, mcp_client: Any = None) -> None:
        self.mcp_client = mcp_client

    async def coder_session_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.coder_usecase import CoderUseCase

        usecase = CoderUseCase(self.mcp_client)
        return dict(await usecase.execute(state))
