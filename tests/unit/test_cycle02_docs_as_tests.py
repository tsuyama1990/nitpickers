import pathlib
import textwrap
from typing import Any
from unittest.mock import patch

import pytest
from _pytest.nodes import Node
from pydantic import ValidationError

from src.domain_models.markdown_test_schema import MarkdownTestBlock
from tests.conftest import MarkdownTestFile


@pytest.fixture
def sample_markdown_content() -> str:
    return textwrap.dedent(
        """
        # UAT tests
        ```python uat-scenario scenario_id="uat-01"
        assert True
        ```
        """
    )


def test_markdown_test_block_valid() -> None:
    block = MarkdownTestBlock(
        execution_language="python",
        scenario_id="scenario-01",
        code_payload="assert True\n",
    )
    assert block.execution_language == "python"
    assert block.scenario_id == "scenario-01"
    assert block.code_payload == "assert True\n"


def test_markdown_test_block_invalid() -> None:
    # Missing fields
    with pytest.raises(ValidationError):
        MarkdownTestBlock(execution_language="python")  # type: ignore[call-arg]

    # Extra fields (extra="forbid")
    with pytest.raises(ValidationError):
        MarkdownTestBlock(
            execution_language="python",
            scenario_id="scenario-02",
            code_payload="pass",
            extra_field="invalid",  # type: ignore[call-arg]
        )


def test_pytest_collect_file_hook_mock(sample_markdown_content: str) -> None:
    """Verifies that the Pytest collector successfully extracts uat-scenario blocks."""

    class MockCollector:
        """A simple mock to bypass Pytest's deep parent/node internal logic."""

        path = pathlib.Path("ALL_SPEC.md")
        collect = MarkdownTestFile.collect

    collector = MockCollector()

    with (
        patch("pathlib.Path.read_text", return_value=sample_markdown_content),
        patch("tests.conftest.MarkdownTestItem.from_parent") as mock_from_parent,
    ):
        # Intercept the Pytest Item construction to verify the parsed block without instantiation issues
        def mock_side_effect(parent: Node, name: str, block: MarkdownTestBlock) -> object:
            class MockItem:
                def __init__(self, name: str, block: MarkdownTestBlock) -> None:
                    self.name = name
                    self.block = block

            return MockItem(name, block)

        mock_from_parent.side_effect = mock_side_effect
        items = list(collector.collect())  # type: ignore[misc]

    assert len(items) == 1

    item: Any = items[0]
    assert item.name == "test_uat-01"
    assert item.block.execution_language == "python"
    assert "assert True" in item.block.code_payload
