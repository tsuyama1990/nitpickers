import os
from typing import Any
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.domain_models.observability_config import ObservabilityConfig
from src.services.workflow import WorkflowService


def test_observability_config_valid() -> None:
    config = ObservabilityConfig(
        langchain_tracing_v2="true",
        langchain_api_key="valid_key",
        langchain_project="valid_project",
    )
    assert config.langchain_tracing_v2 == "true"
    assert config.langchain_api_key == "valid_key"
    assert config.langchain_project == "valid_project"


def test_observability_config_invalid_tracing() -> None:
    with pytest.raises(ValidationError, match="LANGCHAIN_TRACING_V2 must be 'true'"):
        ObservabilityConfig(
            langchain_tracing_v2="false",
            langchain_api_key="valid_key",
            langchain_project="valid_project",
        )


def test_observability_config_empty_key() -> None:
    with pytest.raises(ValidationError, match="Value cannot be empty or whitespace"):
        ObservabilityConfig(
            langchain_tracing_v2="true",
            langchain_api_key="   ",
            langchain_project="valid_project",
        )


@patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "true", "LANGCHAIN_API_KEY": "valid_key", "LANGCHAIN_PROJECT": "test_proj", "JULES_API_KEY": "mock", "E2B_API_KEY": "mock", "OPENROUTER_API_KEY": "mock", "OPENAI_API_KEY": "mock"}, clear=True)
def test_verify_environment_success() -> None:
    with patch("src.services.workflow.ServiceContainer.default"):
        with patch("src.config.Settings.validate_api_keys", return_value=None):
            service = WorkflowService()
            # Should not raise any exception
            service.verify_environment_and_observability()


@patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "false", "LANGCHAIN_API_KEY": "valid_key", "LANGCHAIN_PROJECT": "test_proj", "JULES_API_KEY": "mock", "E2B_API_KEY": "mock", "OPENROUTER_API_KEY": "mock", "OPENAI_API_KEY": "mock"}, clear=True)
def test_verify_environment_failure_tracing() -> None:
    with patch("src.services.workflow.ServiceContainer.default"):
        with patch("src.config.Settings.validate_api_keys", return_value=None):
            service = WorkflowService()
            with pytest.raises(SystemExit):
                service.verify_environment_and_observability()


from pathlib import Path

@patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "true", "LANGCHAIN_API_KEY": "valid_key", "LANGCHAIN_PROJECT": "test_proj", "JULES_API_KEY": "mock", "E2B_API_KEY": "mock", "OPENROUTER_API_KEY": "mock", "OPENAI_API_KEY": "mock"}, clear=True)
def test_verify_environment_spec_dependency_success(tmp_path: Path) -> None:
    # Setup a dummy spec document mentioning an implicit dependency
    spec_dir = tmp_path / "dev_documents" / "system_prompts"
    spec_dir.mkdir(parents=True)
    spec_file = spec_dir / "SPEC.md"
    spec_file.write_text("This feature requires DATABASE_URL to connect to the db.")

    with patch(
        "src.config.settings.paths.documents_dir", tmp_path / "dev_documents"
    ), patch.dict(
        os.environ, {"DATABASE_URL": "postgresql://user:pass@localhost:5432/db"}
    ), patch("src.services.workflow.ServiceContainer.default"), patch("src.config.Settings.validate_api_keys", return_value=None):
        service = WorkflowService()
        service.verify_environment_and_observability()

@patch.dict(os.environ, {"LANGCHAIN_TRACING_V2": "true", "LANGCHAIN_API_KEY": "valid_key", "LANGCHAIN_PROJECT": "test_proj", "JULES_API_KEY": "mock", "E2B_API_KEY": "mock", "OPENROUTER_API_KEY": "mock", "OPENAI_API_KEY": "mock"}, clear=True)
def test_verify_environment_spec_dependency_failure(tmp_path: Path) -> None:
    # Setup a dummy spec document mentioning an implicit dependency
    spec_dir = tmp_path / "dev_documents" / "system_prompts"
    spec_dir.mkdir(parents=True)
    spec_file = spec_dir / "SPEC.md"
    spec_file.write_text("This feature requires DATABASE_URL to connect to the db.")

    with patch("src.config.settings.paths.documents_dir", tmp_path / "dev_documents"), \
         patch("src.services.workflow.ServiceContainer.default"), \
         patch("src.config.Settings.validate_api_keys", return_value=None):
        # Not providing DATABASE_URL
        service = WorkflowService()
        with pytest.raises(SystemExit):
            service.verify_environment_and_observability()
