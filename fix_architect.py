import re

with open('src/nodes/architect.py', 'r') as f:
    content = f.read()

# Replace the specific block of code that we introduced earlier.
# The original code before our modification looked like this:
'''
        except Exception as e:
            console.print(f"[bold red]Failed to setup architect branch: {e}[/bold red]")
            return {"status": "architect_failed", "error": f"Git checkout failed: {e}"}

        context_files = ["dev_documents/ALL_SPEC.md", "README.md", "README_DEVELOPER.md"]
        from anyio import Path

        if await Path("dev_documents/USER_TEST_SCENARIO.md").exists():
            context_files.append("dev_documents/USER_TEST_SCENARIO.md")

        result = await self.jules.execute_command(
            command="Design the system architecture based on ALL_SPEC.md.",
            session_id=f"architect-{timestamp}",
            prompt=instruction,
            target_files=context_files,
            context_files=[],
            require_plan_approval=False,
        )
'''

# The current code has the `gathered_context` block. We will replace everything from
# `# Autonomous file gathering via LLM and MCP Tools`
# to the end of the `result = await getattr...` call.

start_marker = "# Autonomous file gathering via LLM and MCP Tools"
end_marker = "require_plan_approval=False,\n        )"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker) + len(end_marker)

if start_idx != -1 and end_idx != -1:
    new_block = """
        context_files = ["dev_documents/ALL_SPEC.md", "README.md", "README_DEVELOPER.md"]
        from anyio import Path

        if await Path("dev_documents/USER_TEST_SCENARIO.md").exists():
            context_files.append("dev_documents/USER_TEST_SCENARIO.md")

        # Autonomous file gathering via LLM and MCP Tools
        import litellm
        from langchain_core.utils.function_calling import convert_to_openai_tool

        gathered_context = ""
        try:
            async with self.mcp_client as client:
                tools = await client.get_readonly_tools("github")
                litellm_tools = [convert_to_openai_tool(t) for t in tools]
                tools_map = {t.name: t for t in tools}

                # We must provide the repo context dynamically so the tools actually work.
                repo_context = ""
                try:
                    owner, repo_name, _ = await self.jules.git_context.prepare_git_context()
                    repo_context = f"\\nRepository: {owner}/{repo_name}"
                except Exception:
                    repo_context = "\\nRepository: local"

                messages: list[dict[str, Any]] = [
                    {
                        "role": "system",
                        "content": f"You are gathering extra context to design the system architecture.{repo_context}\\n"
                                   "Use the provided tools to explore the repository if needed (e.g., checking package.json, directory structure). "
                                   "Once you have gathered enough context, just reply with 'DONE'. DO NOT design the architecture yet."
                    },
                    {
                        "role": "user",
                        "content": "Please explore the repository to gather any additional useful context beyond the main specifications."
                    }
                ]

                loops = 0
                max_loops = 5

                while loops < max_loops:
                    response = await litellm.acompletion(
                        model=settings.agents.qa_analyst_model,
                        messages=messages,
                        tools=litellm_tools,
                        temperature=0.0,
                    )

                    msg = response.choices[0].message
                    if hasattr(msg, "model_dump"):
                        messages.append(msg.model_dump())
                    elif hasattr(msg, "to_dict"):
                        messages.append(msg.to_dict())
                    elif isinstance(msg, dict):
                        messages.append(msg)
                    else:
                        messages.append({"role": "assistant", "content": msg.content})

                    if getattr(msg, "tool_calls", None):
                        for tc in msg.tool_calls:
                            tool_name = tc.function.name
                            try:
                                import json
                                tool_args = json.loads(tc.function.arguments)
                                # If the tool requires a repo and we didn't get one, try to inject it
                                if "repo" not in tool_args and "owner" in locals() and "repo_name" in locals():
                                    tool_args["repo"] = f"{owner}/{repo_name}"
                            except Exception:
                                tool_args = {}

                            if tool_name in tools_map:
                                try:
                                    res = await tools_map[tool_name].ainvoke(tool_args)
                                    tool_content = str(res)
                                    gathered_context += f"\\n\\n--- File Content (via {tool_name} {tool_args}) ---\\n{tool_content}"
                                except Exception as e:
                                    tool_content = f"Error reading file: {e}"
                            else:
                                tool_content = "Tool not found"

                            messages.append({
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": tool_name,
                                "content": tool_content
                            })
                        loops += 1
                    else:
                        break
        except Exception as e:
            console.print(f"[bold yellow]Warning: Failed to gather context via LLM: {e}[/bold yellow]")

        final_instruction = instruction
        if gathered_context:
            final_instruction += f"\\n\\n=== REPOSITORY CONTEXT ===\\n{gathered_context}"

        result = await getattr(self.jules, "execute_command", getattr(self.jules, "run_session", None))(
            command="Design the system architecture based on ALL_SPEC.md.",
            session_id=f"architect-{timestamp}",
            prompt=final_instruction,
            target_files=context_files,
            context_files=[],
            require_plan_approval=False,
        )
"""
    new_content = content[:start_idx] + new_block.lstrip() + content[end_idx:]
    with open('src/nodes/architect.py', 'w') as f:
        f.write(new_content)
