import json
from collections.abc import Sequence
from typing import Any

import litellm
from langchain_core.tools import BaseTool


async def _execute_tool(
    tc: Any, tools_map: dict[str, BaseTool], extra_tool_args: dict[str, Any] | None
) -> dict[str, Any]:
    tool_name = tc.function.name
    try:
        tool_args = json.loads(tc.function.arguments)
        if extra_tool_args:
            for k, v in extra_tool_args.items():
                if k not in tool_args:
                    tool_args[k] = v
    except Exception:
        tool_args = {}

    if tool_name in tools_map:
        try:
            res = await tools_map[tool_name].ainvoke(tool_args)
            tool_content = str(res)
        except Exception as e:
            tool_content = f"Tool execution failed: {e}"
    else:
        tool_content = f"Error: Tool {tool_name} not found."

    return {
        "role": "tool",
        "tool_call_id": tc.id,
        "name": tool_name,
        "content": tool_content,
    }


def _serialize_message(msg: Any) -> dict[str, Any]:
    if hasattr(msg, "model_dump"):
        return dict(msg.model_dump())
    if hasattr(msg, "to_dict"):
        return dict(msg.to_dict())
    if isinstance(msg, dict):
        return msg
    return {"role": "assistant", "content": getattr(msg, "content", "")}


async def execute_react_loop(
    model: str,
    messages: list[dict[str, Any]],
    tools: Sequence[BaseTool] | None = None,
    max_loops: int = 5,
    temperature: float = 0.0,
    max_tokens: int | None = None,
    extra_tool_args: dict[str, Any] | None = None,
) -> str:
    """
    Executes a standard ReAct (Reasoning and Acting) loop using litellm.
    Automatically handles tool binding, execution, and message history appending.
    Returns the final assistant message string after all tool loops have completed.
    """
    litellm_tools = None
    tools_map = {}
    kwargs: dict[str, Any] = {}

    if tools:
        from langchain_core.utils.function_calling import convert_to_openai_tool

        litellm_tools = [convert_to_openai_tool(t) for t in tools]
        tools_map = {t.name: t for t in tools}

    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens

    loops = 0
    while loops < max_loops:
        if litellm_tools:
            kwargs["tools"] = litellm_tools

        response = await litellm.acompletion(
            model=model, messages=messages, temperature=temperature, **kwargs
        )

        msg = response.choices[0].message
        messages.append(_serialize_message(msg))

        tool_calls = getattr(msg, "tool_calls", None)
        if tool_calls:
            for tc in tool_calls:
                tool_msg = await _execute_tool(tc, tools_map, extra_tool_args)
                messages.append(tool_msg)
            loops += 1
        else:
            return str(msg.content or "")

    return ""
