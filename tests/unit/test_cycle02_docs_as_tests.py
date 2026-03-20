import textwrap
from unittest.mock import MagicMock, mock_open, patch

import pytest
from _pytest.main import Session
from _pytest.nodes import Node
from pydantic import ValidationError

from src.domain_models import MarkdownTestBlock


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


def test_pytest_collect_file_hook_mock() -> None:
    # A simplified mock test of how the hook would behave given a sample markdown
    from tests.conftest import pytest_collect_file

    sample_md = textwrap.dedent(
        """
        # UAT tests
        ```python uat-scenario scenario_id="uat-01"
        assert True
        ```
        """
    )

    mock_parent = MagicMock(spec=Node)
    mock_parent.session = MagicMock(spec=Session)

    import pathlib
    mock_path = pathlib.Path("ALL_SPEC.md")

    # Rather than relying on deep pytest node instantiations in the mock,
    # we can just test the custom collector manually
    from tests.conftest import MarkdownTestFile

    with patch("pathlib.Path.read_text", return_value=sample_md):
        # The easiest way to mock pytest Items and Files without deep _create / nodeid issues
        # is just instantiating without checking _create validation or paths entirely.
        # But we can also use dummy class
        class MockCollector:
            path = pathlib.Path("ALL_SPEC.md")
            # Bind the unbounded method manually
            collect = MarkdownTestFile.collect
            config = MagicMock()

        collector = MockCollector()

        # We also need to mock from_parent inside collect, so let's just
        # mock MarkdownTestItem.from_parent
        with patch("tests.conftest.MarkdownTestItem.from_parent") as mock_from_parent:
            # We must use configure_mock or just a simple object so the MagicMock name attribute doesn't get messed up
            def side_effect(parent: Node, name: str, block: MarkdownTestBlock) -> MagicMock:
                m = MagicMock()
                m.name = name
                m.block = block
                return m
            mock_from_parent.side_effect = side_effect
            items = list(collector.collect())  # type: ignore[call-arg, misc]

    assert len(items) == 1
    assert items[0].name == "test_uat-01"
    assert items[0].block.execution_language == "python"
    assert "assert True" in items[0].block.code_payload
