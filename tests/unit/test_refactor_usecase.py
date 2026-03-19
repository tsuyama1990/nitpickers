from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from src.domain_models.refactor import GlobalRefactorResult
from src.services.jules_client import JulesClient
from src.services.refactor_usecase import RefactorUsecase


@pytest.fixture
def mock_jules_client() -> AsyncMock:
    client = AsyncMock(spec=JulesClient)
    client.run_session.return_value = {"pr_url": "http://github.com/pr/1"}
    return client


@pytest.mark.asyncio
async def test_refactor_usecase_no_issues(tmp_path: Path, mock_jules_client: AsyncMock) -> None:
    usecase = RefactorUsecase(jules_client=mock_jules_client, base_dir=tmp_path)

    with patch("src.services.refactor_usecase.ASTAnalyzer") as mock_analyzer:
        instance = mock_analyzer.return_value
        instance.find_duplicates.return_value = []
        instance.find_complex_functions.return_value = []

        result = await usecase.execute()

        assert isinstance(result, GlobalRefactorResult)
        assert not result.refactorings_applied
        assert "No structural duplicates or complex functions found" in result.summary
        mock_jules_client.run_session.assert_not_called()


@pytest.mark.asyncio
async def test_refactor_usecase_with_duplicates(
    tmp_path: Path, mock_jules_client: AsyncMock
) -> None:
    usecase = RefactorUsecase(jules_client=mock_jules_client, base_dir=tmp_path)

    with patch("src.services.refactor_usecase.ASTAnalyzer") as mock_analyzer:
        instance = mock_analyzer.return_value
        instance.find_duplicates.return_value = [
            [
                {"file": str(tmp_path / "a.py"), "function": "add"},
                {"file": str(tmp_path / "b.py"), "function": "sum_numbers"},
            ]
        ]
        instance.find_complex_functions.return_value = []

        result = await usecase.execute()

        assert result.refactorings_applied
        assert "Refactoring applied to address" in result.summary
        mock_jules_client.run_session.assert_called_once()

        # Check that the prompt was sent
        call_args = mock_jules_client.run_session.call_args[1]
        assert "session_id" in call_args
        assert "prompt" in call_args
        assert "Analyze the complete project context" in call_args["prompt"]
        assert "a.py" in call_args["prompt"]
        assert "b.py" in call_args["prompt"]


@pytest.mark.asyncio
async def test_refactor_usecase_with_complex_functions(
    tmp_path: Path, mock_jules_client: AsyncMock
) -> None:
    usecase = RefactorUsecase(jules_client=mock_jules_client, base_dir=tmp_path)

    with patch("src.services.refactor_usecase.ASTAnalyzer") as mock_analyzer:
        instance = mock_analyzer.return_value
        instance.find_duplicates.return_value = []
        instance.find_complex_functions.return_value = [
            {"file": str(tmp_path / "complex.py"), "function": "do_everything", "complexity": 15}
        ]

        result = await usecase.execute()

        assert result.refactorings_applied
        assert "Refactoring applied to address" in result.summary
        mock_jules_client.run_session.assert_called_once()

        call_args = mock_jules_client.run_session.call_args[1]
        assert "prompt" in call_args
        assert "do_everything" in call_args["prompt"]
        assert "complex.py" in call_args["prompt"]
