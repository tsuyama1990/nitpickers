from collections.abc import Generator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.services.project_setup.template_manager import TemplateManager


@pytest.fixture
def template_manager() -> TemplateManager:
    return TemplateManager()


@pytest.fixture
def mock_settings(tmp_path: Path) -> Generator[MagicMock, None, None]:
    with patch("src.services.project_setup.template_manager.settings") as mock_settings:
        mock_settings.paths.documents_dir = str(tmp_path / "dev_documents")
        yield mock_settings


@pytest.fixture
def mock_cwd(tmp_path: Path) -> Generator[Path, None, None]:
    with patch("src.services.project_setup.template_manager.Path.cwd", return_value=tmp_path):
        yield tmp_path


def test_setup_templates(
    template_manager: TemplateManager, mock_settings: MagicMock, mock_cwd: Path, tmp_path: Path
) -> None:
    templates_path = str(tmp_path / "templates_dest")

    # Mock the internal methods to just verify they are called correctly
    with (
        patch.object(template_manager, "_create_all_spec") as mock_create_all_spec,
        patch.object(template_manager, "_create_user_test_scenario") as mock_create_uts,
        patch.object(template_manager, "copy_default_templates") as mock_copy_templates,
        patch.object(
            template_manager, "_create_env_example", return_value=Path("env_path")
        ) as mock_create_env,
        patch.object(
            template_manager, "_update_gitignore", return_value=Path("git_path")
        ) as mock_update_git,
        patch.object(
            template_manager, "_create_github_workflow", return_value=Path("gh_path")
        ) as mock_create_gh,
    ):
        docs_dir, env_example_path, gitignore_path, github_dir = template_manager.setup_templates(
            templates_path
        )

        expected_docs_dir = Path(mock_settings.paths.documents_dir)

        # Check returned paths
        assert docs_dir == expected_docs_dir
        assert env_example_path == Path("env_path")
        assert gitignore_path == Path("git_path")
        assert github_dir == Path("gh_path")

        # Check directories were created
        assert expected_docs_dir.exists()
        assert Path(templates_path).exists()
        assert (expected_docs_dir / "contracts").exists()
        assert (expected_docs_dir / "system_prompts").exists()

        # Check internal method calls
        mock_create_all_spec.assert_called_once_with(expected_docs_dir)
        mock_create_uts.assert_called_once_with(expected_docs_dir)
        mock_copy_templates.assert_called_once_with(expected_docs_dir / "system_prompts")
        mock_create_env.assert_called_once_with()
        mock_update_git.assert_called_once_with()
        mock_create_gh.assert_called_once_with()


def test_create_all_spec(template_manager: TemplateManager, tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Create first time
    template_manager._create_all_spec(docs_dir)
    all_spec = docs_dir / "ALL_SPEC.md"
    assert all_spec.exists()
    assert "# Project Specifications" in all_spec.read_text()

    # Try creating again when it exists - should not overwrite
    all_spec.write_text("Modified content")
    template_manager._create_all_spec(docs_dir)
    assert all_spec.read_text() == "Modified content"


def test_create_user_test_scenario(template_manager: TemplateManager, tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    # Create first time
    template_manager._create_user_test_scenario(docs_dir)
    uts = docs_dir / "USER_TEST_SCENARIO.md"
    assert uts.exists()
    assert uts.is_file()
    assert "# User Test Scenario & Tutorial Plan" in uts.read_text()

    # Test handling when it's a directory
    uts.unlink()
    uts.mkdir()
    assert uts.is_dir()

    template_manager._create_user_test_scenario(docs_dir)
    assert uts.exists()
    assert uts.is_file()  # The directory should be removed and replaced with a file
    assert "# User Test Scenario & Tutorial Plan" in uts.read_text()


def test_copy_default_templates(template_manager: TemplateManager, tmp_path: Path) -> None:
    system_prompts_dir = tmp_path / "system_prompts"
    system_prompts_dir.mkdir()

    source_dir = tmp_path / "source_templates"
    source_dir.mkdir()
    (source_dir / "template1.md").write_text("template 1 content")
    (source_dir / "template2.md").write_text("template 2 content")

    # Mock the package path to our temp source_dir
    with patch("src.services.project_setup.template_manager.Path") as MockPath:
        # Complex mocking to make Path(src.__file__).parent / "templates" return our source_dir
        # We only mock it for the specific call we care about
        import src

        original_path = Path

        def side_effect(*args: object, **kwargs: object) -> object:
            if args and args[0] == src.__file__:
                mock_src_file = MagicMock()
                mock_src_file.parent = MagicMock()
                mock_src_file.parent.__truediv__.return_value = source_dir
                return mock_src_file
            if args:
                return original_path(str(args[0]), **kwargs)
            return original_path(*args, **kwargs)  # type: ignore[arg-type]

        MockPath.side_effect = side_effect

        template_manager.copy_default_templates(system_prompts_dir)

        assert (system_prompts_dir / "template1.md").exists()
        assert (system_prompts_dir / "template2.md").exists()
        assert (system_prompts_dir / "template1.md").read_text() == "template 1 content"

        # Test skip existing
        (system_prompts_dir / "template1.md").write_text("modified")
        template_manager.copy_default_templates(system_prompts_dir)
        assert (system_prompts_dir / "template1.md").read_text() == "modified"


def test_copy_default_templates_source_missing(
    template_manager: TemplateManager, tmp_path: Path
) -> None:
    system_prompts_dir = tmp_path / "system_prompts"
    system_prompts_dir.mkdir()

    # Source dir doesn't exist
    missing_source_dir = tmp_path / "missing"

    with patch("src.services.project_setup.template_manager.Path") as MockPath:
        import src

        original_path = Path

        def side_effect(*args: object, **kwargs: object) -> object:
            if args and args[0] == src.__file__:
                mock_src_file = MagicMock()
                mock_src_file.parent = MagicMock()
                mock_src_file.parent.__truediv__.return_value = missing_source_dir
                return mock_src_file
            if args:
                return original_path(str(args[0]), **kwargs)
            return original_path(*args, **kwargs)  # type: ignore[arg-type]

        MockPath.side_effect = side_effect

        template_manager.copy_default_templates(system_prompts_dir)
        # Should return without doing anything, no exceptions
        assert list(system_prompts_dir.iterdir()) == []


def test_create_env_example(template_manager: TemplateManager, mock_cwd: Path) -> None:
    env_example_path = template_manager._create_env_example()

    assert env_example_path == mock_cwd / ".ac_cdd" / ".env.example"
    assert env_example_path.exists()
    content = env_example_path.read_text()
    assert "JULES_API_KEY=" in content

    # Should not overwrite if exists
    env_example_path.write_text("Custom env content")
    template_manager._create_env_example()
    assert env_example_path.read_text() == "Custom env content"


def test_update_gitignore(template_manager: TemplateManager, mock_cwd: Path) -> None:
    # First time creation
    gitignore_path = template_manager._update_gitignore()
    assert gitignore_path == mock_cwd / ".gitignore"
    assert gitignore_path.exists()
    content = gitignore_path.read_text()
    assert ".ac_cdd/" in content
    assert "dev_documents/project_state.json" in content

    # Existing file with some contents missing
    gitignore_path.write_text("node_modules/\n")
    template_manager._update_gitignore()
    content = gitignore_path.read_text()
    assert "node_modules/" in content
    assert ".ac_cdd/" in content

    # Existing file with all contents present
    original_content = gitignore_path.read_text()
    template_manager._update_gitignore()
    assert gitignore_path.read_text() == original_content


def test_create_github_workflow(template_manager: TemplateManager, mock_cwd: Path) -> None:
    github_dir = template_manager._create_github_workflow()

    assert github_dir == mock_cwd / ".github"
    ci_path = github_dir / "workflows" / "ci.yml"
    assert ci_path.exists()
    content = ci_path.read_text()
    assert "name: CI" in content
    assert "uv run pytest" in content

    # Should not overwrite if exists
    ci_path.write_text("Custom CI")
    template_manager._create_github_workflow()
    assert ci_path.read_text() == "Custom CI"
