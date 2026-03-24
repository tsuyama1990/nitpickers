import os  # Added import
from pathlib import Path
from typing import Any

from pydantic_ai import Agent, RunContext
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel

from src.config import settings
from src.domain_models import (
    UatAnalysis,
)


def _load_file_content(filepath: str) -> str:
    path = Path(filepath)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _get_system_context() -> str:
    """Injects global context from ALL_SPEC.md and conventions.md if available."""
    context = []

    # Load ALL_SPEC context (Prefer Structured)
    docs_dir = Path(settings.paths.documents_dir)
    structured_spec_path = docs_dir / "ALL_SPEC_STRUCTURED.md"
    raw_spec_path = docs_dir / "ALL_SPEC.md"

    if structured_spec_path.exists():
        content = structured_spec_path.read_text(encoding="utf-8")
        context.append(f"### Project Specifications (Structured)\n{content}")
    elif raw_spec_path.exists():
        content = raw_spec_path.read_text(encoding="utf-8")
        context.append(f"### Project Specifications (Raw)\n{content}")

    # Load conventions.md
    conventions_path = Path(settings.paths.documents_dir) / "conventions.md"
    if conventions_path.exists():
        content = conventions_path.read_text(encoding="utf-8")
        context.append(f"### Coding Conventions\n{content}")

    return "\n\n".join(context)


def _get_openrouter_api_key() -> str:
    """Retrieves OpenRouter API key with fallbacks."""
    api_key = settings.OPENROUTER_API_KEY.get_secret_value() or os.getenv("OPENROUTER_API_KEY")
    if api_key:
        return api_key

    if settings.test_mode:
        return ""

    msg = "OPENROUTER_API_KEY is not set but is required for OpenRouter models."
    raise ValueError(msg)


def get_model(model_name: str) -> Model | str:
    """
    Parses the model name and returns an OpenAIModel with appropriate settings
    if it is an OpenRouter model.
    """
    if model_name.startswith("openrouter/"):
        real_model_name = model_name.replace("openrouter/", "", 1)
        api_key = _get_openrouter_api_key()

        from pydantic_ai.providers.openai import OpenAIProvider

        provider = OpenAIProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        return OpenAIChatModel(
            model_name=real_model_name,
            provider=provider,
        )

    # If gemini/ prefix exists, or just return the string (let PydanticAI handle it)
    if model_name.startswith("gemini/"):
        return model_name.replace("gemini/", "", 1)

    return model_name


# --- Agents ---
# Auditor Agent is deprecated/removed in favor of LLMReviewer.

# Lazy initialization to avoid requiring API keys at import time
_qa_analyst_agent: Agent[Any, UatAnalysis] | None = None


def get_qa_analyst_agent() -> Agent[Any, UatAnalysis]:
    """Get or create the QA Analyst agent instance."""
    global _qa_analyst_agent  # noqa: PLW0603
    if _qa_analyst_agent is None:
        _qa_analyst_agent = Agent(
            model=get_model(settings.agents.qa_analyst_model),
            system_prompt=settings.get_prompt_content(
                "UAT_DESIGN.md", default="You are a QA Analyst."
            ),
        )

        @_qa_analyst_agent.system_prompt
        def qa_analyst_system_prompt(_ctx: RunContext[Any]) -> str:
            return _get_system_context()

    return _qa_analyst_agent
