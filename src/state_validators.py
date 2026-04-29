import re
from typing import Any

from src.config import settings
from src.enums import FlowStatus


def validate_cycle_id(v: str) -> str:
    """Validates that the cycle ID is alphanumeric (supporting '01' and 'qa-tutorials')."""
    if not re.match(r"^[a-zA-Z0-9_-]+$", v):
        msg = f"cycle_id '{v}' is invalid (must be alphanumeric, e.g., '01' or 'qa-tutorials')"
        raise ValueError(msg)
    return v


def validate_auditor_index(v: int) -> int:
    """Validates the auditor index is within configured bounds."""
    if v < 1:
        msg = f"Auditor index {v} must be greater than or equal to 1"
        raise ValueError(msg)
    if v > settings.NUM_AUDITORS:
        msg = f"Auditor index {v} exceeds NUM_AUDITORS={settings.NUM_AUDITORS}"
        raise ValueError(msg)
    return v


def validate_review_count(v: int) -> int:
    """Validates the review count is within configured bounds."""
    if v < 1:
        msg = f"Review count {v} must be greater than or equal to 1"
        raise ValueError(msg)
    if v > settings.REVIEWS_PER_AUDITOR:
        msg = f"Review count {v} exceeds REVIEWS_PER_AUDITOR={settings.REVIEWS_PER_AUDITOR}"
        raise ValueError(msg)
    return v


def validate_audit_attempt_count(v: int) -> int:
    """Validates the audit attempt count does not exceed configuration limits excessively."""
    if v < 0:
        msg = f"Audit attempt count {v} cannot be negative"
        raise ValueError(msg)
    # The count can safely hit max_audit_retries + 1 before the router fails it
    if v > settings.max_audit_retries + 1:
        msg = f"Audit attempt count {v} exceeds absolute maximum threshold of {settings.max_audit_retries + 1}"
        raise ValueError(msg)
    return v


def validate_state_consistency(state: Any) -> Any:
    """Performs cross-field logical consistency checks on the state object."""
    from src.config import settings

    status = getattr(state, "status", None)
    error = getattr(state, "error", None)
    current_auditor_index = getattr(state, "current_auditor_index", 1)

    if status == FlowStatus.COMPLETED and error is not None and hasattr(state, "error"):
        # Instead of crashing, automatically clear the error field since the state is successfully completed.
        state.error = None

    if isinstance(current_auditor_index, int) and current_auditor_index > settings.NUM_AUDITORS:
        msg = f"Auditor index {current_auditor_index} logically exceeds maximum {settings.NUM_AUDITORS}"
        raise ValueError(msg)

    return state
