with open('src/services/refactor_usecase.py') as f:
    content = f.read()

content = content.replace('''        # Securely generate Session ID to prevent session fixation attacks
        secure_token = secrets.token_urlsafe(32)
        session_id = f"master-integrator-{settings.current_session_id}-{secure_token}"

        try:''', '''        try:''')

content = content.replace('''                response = await self.llm_reviewer._ainvoke_with_tools(
                    prompt=orchestration_prompt, model=model, tools=tools
                )''', '''                _response = await self.llm_reviewer._ainvoke_with_tools(
                    prompt=orchestration_prompt, model=model, tools=tools
                )''')

with open('src/services/refactor_usecase.py', 'w') as f:
    f.write(content)
