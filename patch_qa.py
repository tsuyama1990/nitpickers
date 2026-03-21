with open('src/services/qa_usecase.py') as f:
    content = f.read()

content = content.replace('''            # Wait for Jules to complete script generation
            result = await self.jules.wait_for_completion(session_id)''', '''            # Use LLMReviewer to generate code
            async with self.mcp_client as client:
                tools = await client.get_readonly_tools(server_name="github")
                result = await self.llm_reviewer._ainvoke_with_tools(prompt=qa_prompt, model=settings.reviewer.smart_model, tools=tools)''')

with open('src/services/qa_usecase.py', 'w') as f:
    f.write(content)
