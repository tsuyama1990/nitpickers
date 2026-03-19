import os
from unittest.mock import patch

from src.domain_models.tracing import LangSmithConfig, TracingMetadata
from src.services.tracing import TracingService


def test_tracing_metadata_to_langchain_kwargs() -> None:
    metadata = TracingMetadata(
        session_id="session-123",
        execution_type="jules_session",
        git_branch="feature/branch",
        custom_metadata={"key": "value"},
    )

    kwargs = metadata.to_langchain_kwargs()

    assert kwargs == {
        "tags": ["jules_session", "branch:feature/branch"],
        "metadata": {"session_id": "session-123", "key": "value"},
    }


def test_tracing_metadata_no_branch() -> None:
    metadata = TracingMetadata(
        session_id="session-123",
        execution_type="cli_run",
    )

    kwargs = metadata.to_langchain_kwargs()

    assert kwargs == {"tags": ["cli_run"], "metadata": {"session_id": "session-123"}}


def test_tracing_service_is_enabled() -> None:
    with patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "false"}):
        config = LangSmithConfig(tracing_enabled=False)
        config.tracing_enabled = True
        service = TracingService(config)
        assert service.is_enabled is True

        config = LangSmithConfig(tracing_enabled=False)
        service = TracingService(config)
        assert service.is_enabled is False

    with patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "true"}):
        config = LangSmithConfig(tracing_enabled=False)
        service = TracingService(config)
        assert service.is_enabled is True
