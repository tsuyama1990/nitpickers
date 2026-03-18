import pytest
from pydantic import ValidationError

from src.domain_models import ConflictRegistryItem, E2BExecutionResult


def test_conflict_registry_item_valid() -> None:
    item = ConflictRegistryItem(
        file_path="src/main.py",
        conflict_markers=["<<<<<<< HEAD", "=======", ">>>>>>> master"],
    )

    assert item.file_path == "src/main.py"
    assert len(item.conflict_markers) == 3
    assert item.resolution_attempts == 0
    assert item.resolved is False


def test_conflict_registry_item_invalid_missing_fields() -> None:
    with pytest.raises(ValidationError):
        # Missing conflict_markers
        ConflictRegistryItem(file_path="src/main.py") # type: ignore[call-arg]


def test_e2b_execution_result_valid() -> None:
    result = E2BExecutionResult(
        stdout="Test passed",
        stderr="",
        exit_code=0,
        coverage_report="Coverage 100%",
    )

    assert result.stdout == "Test passed"
    assert result.exit_code == 0
    assert result.coverage_report == "Coverage 100%"


def test_e2b_execution_result_invalid_exit_code() -> None:
    with pytest.raises(ValidationError):
        # exit_code should be int, Pydantic strict mode (or just coercing strings failing if we used strict config but default coerces '0' to int 0, 'fail' throws)
        E2BExecutionResult(exit_code="fail") # type: ignore[arg-type]


def test_e2b_execution_result_coercion() -> None:
    result = E2BExecutionResult(exit_code="0") # type: ignore[arg-type]
    assert result.exit_code == 0
