import base64
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from src.domain_models import FixPlanSchema, MultiModalArtifact, UatExecutionState
from src.enums import FlowStatus, WorkPhase
from src.services.llm_reviewer import LLMReviewer
from src.state import CycleState


def test_fix_plan_schema_valid() -> None:
    data = {
        "defect_description": "The button class was misspelled in the test, but the code is correct.",
        "patches": [
            {
                "target_file": "src/main.py",
                "git_diff_patch": "--- a/tests/test_main.py\n+++ b/tests/test_main.py\n- btn = page.locator('.btn-primary')\n+ btn = page.locator('.btn-submit')",
            }
        ]
    }
    schema = FixPlanSchema(**data)
    assert schema.patches[0].target_file == "src/main.py"
    assert "misspelled" in schema.defect_description


def test_fix_plan_schema_invalid_extra_field() -> None:
    data = {
        "defect_description": "Fix it.",
        "patches": [
            {
                "target_file": "src/main.py",
                "git_diff_patch": "...",
            }
        ],
        "extra_field": "Should fail",
    }
    with pytest.raises(ValidationError):
        FixPlanSchema(**data)


@pytest.mark.asyncio
async def test_diagnose_uat_failure_success(tmp_path: Path) -> None:
    reviewer = LLMReviewer()

    # Create dummy artifact files
    img_path = tmp_path / "screenshot.png"
    img_path.write_bytes(b"dummy image data")

    uat_state = UatExecutionState(
        exit_code=1,
        stdout="Tests failed",
        stderr="Traceback...",
        artifacts=[
            MultiModalArtifact(
                test_id="test_login",
                screenshot_path=str(img_path),
                traceback="Button not found",
                console_logs=[],
            )
        ],
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[
        0
    ].message.content = (
        '{"defect_description": "Test", "patches": [{"target_file": "src/main.py", "git_diff_patch": "patch"}]}'
    )

    with patch(
        "src.services.llm_reviewer.litellm.acompletion", new_callable=AsyncMock
    ) as mock_acompletion:
        mock_acompletion.return_value = mock_response

        plan = await reviewer.diagnose_uat_failure(uat_state, "Instruction", "model-test")

        assert plan.patches[0].target_file == "src/main.py"
        assert plan.defect_description == "Test"
        assert plan.patches[0].git_diff_patch == "patch"

        # Verify base64 encoding was passed correctly
        call_args = mock_acompletion.call_args[1]
        messages = call_args["messages"]
        user_content = messages[1]["content"]

        # Ensure image URL content exists
        has_image = False
        for part in user_content:
            if isinstance(part, dict) and part.get("type") == "image_url":
                has_image = True
                url = part["image_url"]["url"]
                expected_b64 = base64.b64encode(b"dummy image data").decode("utf-8")
                assert url == f"data:image/png;base64,{expected_b64}"

        assert has_image, "Image URL was not added to the prompt"


@pytest.mark.asyncio
async def test_diagnose_uat_failure_invalid_json(tmp_path: Path) -> None:
    reviewer = LLMReviewer()

    uat_state = UatExecutionState(
        exit_code=1,
        stdout="Tests failed",
        stderr="Traceback...",
        artifacts=[],
    )

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Invalid JSON String"

    with patch(
        "src.services.llm_reviewer.litellm.acompletion", new_callable=AsyncMock
    ) as mock_acompletion:
        mock_acompletion.return_value = mock_response

        plan = await reviewer.diagnose_uat_failure(uat_state, "Instruction", "model-test")

        assert plan.patches[0].target_file == "Unknown"
        assert "SYSTEM_ERROR" in plan.defect_description


@pytest.mark.asyncio
async def test_auditor_usecase_routing() -> None:
    from src.domain_models.fix_plan_schema import FilePatch
    mock_reviewer = MagicMock(spec=LLMReviewer)

    valid_plan = FixPlanSchema(
        defect_description="A bug", patches=[FilePatch(target_file="src/test.py", git_diff_patch="patch")]
    )
    mock_reviewer.diagnose_uat_failure = AsyncMock(return_value=valid_plan)

    from src.services.auditor_usecase import UATAuditorUseCase

    usecase = UATAuditorUseCase(mock_reviewer)

    from src.state import UATState

    state = CycleState(
        cycle_id="01",
        current_phase=WorkPhase.CODER,
        uat=UATState(
            uat_execution_state=UatExecutionState(exit_code=1, stdout="", stderr="", artifacts=[])
        ),
    )

    result = await usecase.execute(state)

    assert result["status"] == FlowStatus.RETRY_FIX
    assert result["current_fix_plan"] == valid_plan
    assert result["uat_execution_state"] is None
    assert result["uat_retry_count"] == 1
