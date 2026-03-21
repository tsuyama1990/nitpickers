with open('src/services/auditor_usecase.py') as f:
    content = f.read()

content = content.replace('''    def __init__(
        self,
        jules_client: JulesClient,
        git_manager: GitManager,
        llm_reviewer: LLMReviewer,
        mcp_client: Any = None,
    ) -> None:
        if not jules_client or not git_manager or not llm_reviewer:
            msg = "JulesClient, GitManager, and LLMReviewer must be provided"
            raise ValueError(msg)
        self.jules = jules_client
        self.git = git_manager
        self.llm_reviewer = llm_reviewer
        self.mcp_client = mcp_client or McpClientManager()''', '''    def __init__(
        self,
        mcp_client: McpClientManager | None = None,
        git_manager: Any = None,
        llm_reviewer: LLMReviewer | None = None,
    ) -> None:
        self.mcp_client = mcp_client or McpClientManager()
        self.git = git_manager
        self.llm_reviewer = llm_reviewer or LLMReviewer()''')

with open('src/services/auditor_usecase.py', 'w') as f:
    f.write(content)
