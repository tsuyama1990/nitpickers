import pytest

from src.config import settings
from src.state_validators import validate_auditor_index


def test_validate_auditor_index() -> None:
    assert validate_auditor_index(1) == 1
    assert validate_auditor_index(settings.NUM_AUDITORS) == settings.NUM_AUDITORS

    with pytest.raises(ValueError, match="Auditor index 0 must be greater than or equal to 1"):
        validate_auditor_index(0)

    with pytest.raises(
        ValueError,
        match=f"Auditor index {settings.NUM_AUDITORS + 1} exceeds NUM_AUDITORS={settings.NUM_AUDITORS}",
    ):
        validate_auditor_index(settings.NUM_AUDITORS + 1)
