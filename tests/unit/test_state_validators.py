import re

import pytest

from src.state_validators import validate_cycle_id


def test_validate_cycle_id_valid() -> None:
    """Test validate_cycle_id with valid inputs."""
    assert validate_cycle_id("01") == "01"
    assert validate_cycle_id("99") == "99"
    assert validate_cycle_id("00") == "00"


def test_validate_cycle_id_invalid() -> None:
    """Test validate_cycle_id with invalid inputs."""
    invalid_inputs = [
        "1",     # Too short
        "100",   # Too long
        "ab",    # Non-numeric
        "",      # Empty string
        " 01",   # Leading space
        "01 ",   # Trailing space
        "-1",    # Negative sign
        "1.0",   # Decimal point
    ]

    for invalid_input in invalid_inputs:
        expected_msg = f"cycle_id '{invalid_input}' is invalid (must be exactly two digits, e.g., '01')"
        with pytest.raises(ValueError, match=re.escape(expected_msg)):
            validate_cycle_id(invalid_input)
