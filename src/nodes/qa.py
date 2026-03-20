from typing import Any

from src.state import CycleState


class QaNodes:
    def __init__(self, jules: Any, git: Any, llm_reviewer: Any, mcp_manager: Any = None) -> None:
        from src.config import settings
        from src.domain_models.config import McpServerConfig
        from src.services.mcp_client_manager import McpClientManager

        self.jules = jules
        self.git = git
        self.llm_reviewer = llm_reviewer
        if mcp_manager is None:
            config = McpServerConfig(e2b_api_key=settings.E2B_API_KEY)
            self.mcp_manager = McpClientManager(config)
        else:
            self.mcp_manager = mcp_manager

        # Internal LLM for tool binding
        from langchain_openai import ChatOpenAI
        self.llm = ChatOpenAI(model=settings.reviewer.fast_model)

    async def qa_session_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.qa_usecase import QaUseCase

        async with self.mcp_manager as mcp_client:
            tools = await mcp_client.get_tools()
            _llm_with_tools = self.llm.bind_tools(tools)

        usecase = QaUseCase(self.jules, self.git, self.llm_reviewer)
        return dict(await usecase.execute_qa_session(state))

    async def qa_auditor_node(self, state: CycleState) -> dict[str, Any]:
        from src.services.qa_usecase import QaUseCase

        usecase = QaUseCase(self.jules, self.git, self.llm_reviewer)
        return dict(await usecase.execute_qa_audit(state))
