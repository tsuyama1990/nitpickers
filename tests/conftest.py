import os

# Set dummy API keys before any tests run, to prevent pydantic-ai from complaining
# during module import and inspection.
os.environ["OPENAI_API_KEY"] = "dummy_key_for_test"
os.environ["ANTHROPIC_API_KEY"] = "dummy_key_for_test"
os.environ["GEMINI_API_KEY"] = "dummy_key_for_test"
os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_test"
os.environ["JULES_API_KEY"] = "dummy_key_for_test"
os.environ["E2B_API_KEY"] = "dummy_key_for_test"

import re
import runpy
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from src.domain_models.markdown_test_schema import MarkdownTestBlock

# Also set models to dummy values to prevent provider resolution errors
os.environ["AC_CDD_AUDITOR_MODEL"] = "openai:gpt-4o"
os.environ["AC_CDD_QA_ANALYST_MODEL"] = "openai:gpt-4o"
os.environ["AC_CDD_REVIEWER__SMART_MODEL"] = "openai:gpt-4o"
os.environ["AC_CDD_REVIEWER__FAST_MODEL"] = "openai:gpt-3.5-turbo"


class MarkdownTestItem(pytest.Item):
    """A pytest item for executing a code block from a Markdown file."""

    def __init__(self, name: str, parent: pytest.File, block: MarkdownTestBlock) -> None:
        super().__init__(name, parent)
        self.block = block

    def runtest(self) -> None:
        # Create a temporary file, run it using runpy to get accurate stack traces
        with tempfile.NamedTemporaryFile(
            suffix=".py", delete=False, mode="w", encoding="utf-8"
        ) as tf:
            tf.write(self.block.code_payload)
            temp_path = tf.name

        try:
            # Execute the generated python file natively
            runpy.run_path(temp_path, init_globals={})
        finally:
            path_obj = Path(temp_path)
            if path_obj.exists():
                path_obj.unlink()


class MarkdownTestFile(pytest.File):
    """A pytest file collector for Markdown specifications."""

    def collect(self) -> Iterable[MarkdownTestItem]:
        content = Path(self.path).read_text(encoding="utf-8")

        # Regex to find fenced python code blocks tagged with `uat-scenario`
        # and extracting an optional `scenario_id="..."` or `id="..."`
        # Example: ```python uat-scenario scenario_id="01-01"
        pattern = re.compile(
            r"^```python\s+(?:.*?\b)?uat-scenario(?:.*?\bscenario_id=[\"']([^\"']+)[\"'])?.*?\n(.*?)^```",
            re.MULTILINE | re.DOTALL,
        )

        matches = pattern.finditer(content)
        for i, match in enumerate(matches, 1):
            scenario_id_match = match.group(1)
            code_payload = match.group(2)
            scenario_id = scenario_id_match if scenario_id_match else f"scenario-{i}"

            block = MarkdownTestBlock(
                execution_language="python", scenario_id=scenario_id, code_payload=code_payload
            )

            # Use the scenario ID as the test name
            yield MarkdownTestItem.from_parent(self, name=f"test_{scenario_id}", block=block)


def pytest_collect_file(file_path: Any, parent: Any) -> pytest.File | None:
    """Pytest hook for collecting test files."""
    if file_path.name in ("ALL_SPEC.md", "README.md", "UAT.md"):
        # We also support UAT.md or any file matching these for docs-as-tests
        return MarkdownTestFile.from_parent(parent, path=file_path)
    return None
