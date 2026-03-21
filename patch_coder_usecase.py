with open('src/services/coder_usecase.py') as f:
    content = f.read()

content = content.replace('''from src.services.jules_client import JulesClient''', '''from src.services.mcp_client_manager import McpClientManager
from src.services.llm_reviewer import LLMReviewer
import json''')

content = content.replace('''    def __init__(self, jules_client: JulesClient) -> None:
        if not jules_client:
            msg = "JulesClient must be injected into CoderUseCase"
            raise ValueError(msg)
        self.jules = jules_client''', '''    def __init__(self, mcp_client: McpClientManager | None = None, llm_reviewer: LLMReviewer | None = None) -> None:
        self.mcp_client = mcp_client or McpClientManager()
        self.llm_reviewer = llm_reviewer or LLMReviewer()''')

content = content.replace('''        # We use JulesClient run_session with tools to generate edits
        prompt = self._build_prompt(state)

        # Build list of active spec and code files
        context_files = [str(f) for f in self._get_context_files(state)]

        try:
            result = await self.jules.run_session(
                session_id=settings.current_session_id,
                prompt=prompt,
                files=context_files,
                execution_type="coder"
            )''', '''        prompt = self._build_prompt(state)
        context_files = [str(f) for f in self._get_context_files(state)]

        try:
            async with self.mcp_client as client:
                tools = await client.get_readonly_tools(server_name="github")
                model = settings.reviewer.smart_model

                coder_prompt = (
                    "You are the Coder agent.\\n"
                    f"{prompt}\\n\\n"
                    f"Context files: {context_files}\\n"
                    "Use tools to read files, then output a JSON list of patches.\\n"
                    "Output valid JSON."
                )

                response = await self.llm_reviewer._ainvoke_with_tools(
                    prompt=coder_prompt, model=model, tools=tools
                )
                result = {"raw_output": response} # fallback dict shape''')

with open('src/services/coder_usecase.py', 'w') as f:
    f.write(content)
