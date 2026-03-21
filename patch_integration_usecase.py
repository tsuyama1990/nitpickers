with open('src/services/integration_usecase.py') as f:
    content = f.read()

content = content.replace('''from src.services.jules_client import JulesClient''', '''from src.services.mcp_client_manager import McpClientManager
from src.services.llm_reviewer import LLMReviewer
from src.config import settings
import json''')

content = content.replace('''    def __init__(
        self, jules_client: JulesClient | None = None, max_retries: int | None = None
    ) -> None:
        self.jules = jules_client or JulesClient()''', '''    def __init__(
        self,
        mcp_client: McpClientManager | None = None,
        llm_reviewer: LLMReviewer | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.mcp_client = mcp_client or McpClientManager()
        self.llm_reviewer = llm_reviewer or LLMReviewer()''')

content = content.replace('''        # Ensure session exists
        if not state.master_integrator_session_id:
            state.master_integrator_session_id = self.jules.create_master_integrator_session()
            logger.info(f"Created Master Integrator Session: {state.master_integrator_session_id}")

        for i, item in enumerate(state.unresolved_conflicts):
            if item.resolved:
                continue

            try:
                await self._resolve_single_file(state.master_integrator_session_id, item, repo_path)
            except Exception as e:
                logger.error(f"Failed to resolve file {item.file_path}: {e}")
                msg = f"Failed to resolve {item.file_path}: {e}"
                raise MaxRetriesExceededError(msg) from e

            state.unresolved_conflicts[i] = item

        return state''', '''        # Master Integrator loop logic via MCP.
        # Now handles write tools.
        if not state.master_integrator_session_id:
            state.master_integrator_session_id = "master-integrator-session"
            logger.info(f"Created Master Integrator Session: {state.master_integrator_session_id}")

        for i, item in enumerate(state.unresolved_conflicts):
            if item.resolved:
                continue

            try:
                await self._resolve_single_file(state.master_integrator_session_id, item, repo_path)
            except Exception as e:
                logger.error(f"Failed to resolve file {item.file_path}: {e}")
                msg = f"Failed to resolve {item.file_path}: {e}"
                raise MaxRetriesExceededError(msg) from e

            state.unresolved_conflicts[i] = item

        return state''')

content = content.replace('''            # Send to Jules
            response_code = await self.jules.send_message_to_session(
                session_id, prompt, message_history
            )''', '''            # Use MCP GitHub read tools maybe, or just LLM
            async with self.mcp_client as client:
                model = settings.reviewer.smart_model
                response_code = await self.llm_reviewer._ainvoke_with_tools(
                    prompt=prompt, model=model, tools=[]
                )''')

with open('src/services/integration_usecase.py', 'w') as f:
    f.write(content)
