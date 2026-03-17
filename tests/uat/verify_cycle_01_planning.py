import pytest
from ac_cdd_core.domain_models import ArchitectCriticResponse

def test_architect_critic_response_schema():
    # Test valid passing schema
    valid_pass = ArchitectCriticResponse(is_passed=True, feedback=[])
    assert valid_pass.is_passed is True
    assert valid_pass.feedback == []

    # Test valid failing schema
    valid_fail = ArchitectCriticResponse(is_passed=False, feedback=["Flaw 1", "Flaw 2"])
    assert valid_fail.is_passed is False
    assert len(valid_fail.feedback) == 2

    # Verify extra fields are forbidden
    with pytest.raises(ValueError):
        ArchitectCriticResponse(is_passed=True, feedback=[], unknown_field="invalid")
