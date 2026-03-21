for filepath in ['src/nodes/architect_critic.py', 'src/nodes/coder_critic.py']:
    with open(filepath) as f:
        content = f.read()

    content = content.replace('''    def __init__(self, jules_client: Any) -> None:
        self.jules = jules_client
        self.evaluator = SelfCriticEvaluator(jules_client)''', '''    def __init__(self, mcp_client: Any = None) -> None:
        self.mcp_client = mcp_client
        self.evaluator = SelfCriticEvaluator(mcp_client)''')

    content = content.replace('''    def __init__(self, jules_client: Any) -> None:
        self.jules = jules_client''', '''    def __init__(self, mcp_client: Any = None) -> None:
        self.mcp_client = mcp_client''')

    content = content.replace('''self.evaluator = SelfCriticEvaluator(self.jules)''', '''self.evaluator = SelfCriticEvaluator(self.mcp_client)''')

    with open(filepath, 'w') as f:
        f.write(content)
