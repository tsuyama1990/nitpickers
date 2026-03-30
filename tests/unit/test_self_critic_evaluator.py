from unittest.mock import AsyncMock, MagicMock

import pytest

from src.services.self_critic_evaluator import SelfCriticEvaluator


@pytest.fixture
def mock_jules() -> MagicMock:
    jules = MagicMock()
    jules._get_session_url.return_value = "https://mock.url/sessions/123"
    jules._send_message = AsyncMock()
    return jules


@pytest.mark.asyncio
async def test_critic_approved(mock_jules: MagicMock) -> None:
    evaluator = SelfCriticEvaluator(mock_jules)
    mock_jules.wait_for_completion = AsyncMock(
        return_value={
            "status": "success",
            "raw": {
                "outputs": [
                    {"text": '{"is_approved": true, "vulnerabilities": [], "suggestions": []}'}
                ]
            },
        }
    )

    result = await evaluator.evaluate("session-123")

    assert result.is_approved is True
    assert result.vulnerabilities == []


@pytest.mark.asyncio
async def test_critic_rejected_retry_loop(mock_jules: MagicMock) -> None:
    evaluator = SelfCriticEvaluator(mock_jules)
    mock_jules.wait_for_completion = AsyncMock(
        return_value={
            "status": "success",
            "raw": {
                "outputs": [
                    {
                        "text": '{"is_approved": false, "vulnerabilities": ["N+1 query"], "suggestions": ["Use JOIN"]}'
                    }
                ]
            },
        }
    )

    result = await evaluator.evaluate("session-123")

    assert result.is_approved is False
    assert result.vulnerabilities == ["N+1 query"]
    assert result.suggestions == ["Use JOIN"]


@pytest.mark.asyncio
async def test_critic_with_custom_template(mock_jules: MagicMock) -> None:
    evaluator = SelfCriticEvaluator(mock_jules)
    mock_jules.wait_for_completion = AsyncMock(
        return_value={
            "status": "success",
            "raw": {
                "outputs": [
                    {"text": '{"is_approved": true, "vulnerabilities": [], "suggestions": []}'}
                ]
            },
        }
    )

    # Use a different existing template for testing
    result = await evaluator.evaluate(
        "session-123", template_name="POST_AUDIT_REFACTOR_INSTRUCTION.md", cycle_id="01"
    )

    assert result.is_approved is True
    # Verify that it called _send_message with something containing "Cycle 01"
    # because of the substitution
    args, _ = mock_jules._send_message.call_args
    assert "Cycle 01" in args[1]
