from unittest.mock import patch

import pytest

from src.utils import check_api_key


def test_check_api_key_no_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test when no API keys are present."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    # Mock load_dotenv to avoid it loading from any actual .env file
    with patch("src.utils.load_dotenv"):
        assert check_api_key() is False


def test_check_api_key_google_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test when only GOOGLE_API_KEY is present."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_key")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with patch("src.utils.load_dotenv"):
        assert check_api_key() is True


def test_check_api_key_openrouter_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test when only OPENROUTER_API_KEY is present."""
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_openrouter_key")

    with patch("src.utils.load_dotenv"):
        assert check_api_key() is True


def test_check_api_key_both_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test when both keys are present."""
    monkeypatch.setenv("GOOGLE_API_KEY", "test_google_key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_openrouter_key")

    with patch("src.utils.load_dotenv"):
        assert check_api_key() is True
