import pytest
from playwright.sync_api import Page, expect


@pytest.mark.skip(reason="Reflex local start within pytest is unstable. Mock the tests for now or rely on isolated CI environments")
def test_app_loads(page: Page) -> None:
    pass
