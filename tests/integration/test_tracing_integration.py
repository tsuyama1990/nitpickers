import os
from unittest.mock import patch

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from src.domain_models.tracing import LangSmithConfig, TracingMetadata
from src.services.tracing import TracingService


def dummy_node(state: dict) -> dict:
    return {"status": "success"}


def create_mock_graph():
    builder = StateGraph(dict)
    builder.add_node("dummy", dummy_node)
    builder.add_edge(START, "dummy")
    builder.add_edge("dummy", END)
    return builder.compile()


@pytest.mark.asyncio
async def test_graph_execution_with_context() -> None:
    metadata = TracingMetadata(
        session_id="integration-test-session",
        execution_type="test_run",
        git_branch="test/integration",
        custom_metadata={"test": True},
    )

    kwargs = metadata.to_langchain_kwargs()
    config = RunnableConfig(tags=kwargs.get("tags"), metadata=kwargs.get("metadata"))

    graph = create_mock_graph()

    initial_state = {"status": "start"}
    final_state = await graph.ainvoke(initial_state, config=config)

    assert final_state["status"] == "success"


@pytest.mark.asyncio
async def test_missing_api_key_fallback() -> None:
    config = LangSmithConfig(tracing_enabled=True, api_key=None)
    service = TracingService(config)

    graph = create_mock_graph()

    with (
        patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "true", "LANGCHAIN_API_KEY": ""}),
        patch("src.services.tracing.logger.warning") as mock_logger,
    ):
        with service.trace_context("test_project"):
            final_state = await graph.ainvoke({"status": "start"})
            assert final_state["status"] == "success"

        mock_logger.assert_called_once()
        assert "LangSmith tracing enabled but no API key provided" in mock_logger.call_args[0][0]
