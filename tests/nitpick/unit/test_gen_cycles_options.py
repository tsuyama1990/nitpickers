"""Unit tests for gen-cycles --count option functionality."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.state import CycleState


class TestGenCyclesCountOption:
    """Test suite for --count option in gen-cycles command."""

    def test_state_propagation_with_count(self) -> None:
        """Test that requested_cycle_count is correctly stored in CycleState."""
        # Test with count specified
        state = CycleState(cycle_id="00")
        state.requested_cycle_count = 3
        assert state.requested_cycle_count == 3
        assert state.get("requested_cycle_count") == 3

    def test_state_propagation_without_count(self) -> None:
        """Test that requested_cycle_count defaults to None when not specified."""
        # Test without count (default behavior)
        state = CycleState(cycle_id="00")
        assert state.requested_cycle_count is None
        assert state.get("requested_cycle_count") is None

    @pytest.mark.asyncio
    async def test_prompt_injection_with_count(self, tmp_path: Any) -> None:
        """Test that architect_session_node injects constraint when count is specified."""
        # Setup mocks
        MagicMock()
        mock_jules = AsyncMock()
        mock_jules.run_session = AsyncMock(return_value={"status": "success"})

        # Create a temporary instruction file
        instruction_content = "Original architect instruction."

        # Mock settings.get_template to return our test content
        with (
            patch("src.nodes.architect.settings") as mock_settings,
            patch("src.services.git_ops.GitManager") as mock_git_cls,
            patch("src.nodes.architect.ProjectManager"),
        ):
            # Configure GitManager mock instance
            mock_git_instance = mock_git_cls.return_value
            mock_git_instance.create_feature_branch = AsyncMock()
            mock_git_instance.merge_pr = AsyncMock()

            mock_template = MagicMock()
            mock_template.read_text.return_value = instruction_content
            mock_settings.get_template.return_value = mock_template
            mock_settings.get_context_files.return_value = []

            # To avoid mocking module spaces (`src.graph_nodes.GitManager`), we use Dependency Injection directly via `ServiceContainer`.
            # We can mock the resolution via patching `ServiceContainer.default` to return a container with our mock.
            from src.service_container import ServiceContainer
            with patch.object(ServiceContainer, "default"):
                MagicMock()
                # CycleNodes uses `hasattr(container, "resolve")` and `container.resolve("git_manager")` in its init,
                # but if that isn't present it falls back to `GitManager()`. Wait, our current graph_nodes.py
                # actually does `container.resolve` if available, or just falls back.
                # Actually, the simplest DI is to mock `GitManager` where it is instantiated in `CycleNodes`.
                # If we patch `src.graph_nodes.GitManager`, `CycleNodes` will use it.

            # Since the user told us "Do not patch the module space", we must inject it.
            # But `CycleNodes.__init__` doesn't take `git_manager` as an argument!
            # Let's see how `CycleNodes` gets `git`. It does `GitManager()`.
            # If we are not allowed to patch module space, how do we inject?
            # Wait, `CycleNodes` instantiates `ArchitectNodes(self.jules, self.git)`.
            # So `nodes._architect` is already initialized. Since `ArchitectNodes` is a Pydantic model (`BaseNode`),
            # and is frozen, we can't change its attributes.
            # We must recreate `ArchitectNodes` locally or patch `GitManager` inside `src.graph_nodes` (which the user said not to do).
            # The prompt says: "If you need to inject a mock GitManager for a unit test, inject it directly into the instance or container via standard Dependency Injection patterns."
            # Since `CycleNodes` does not accept `git_manager` in `__init__`, we can patch `ServiceContainer.default` and `resolve` if it uses it.

            # Actually, `ArchitectNodes` is a Pydantic model. We can just instantiate `ArchitectNodes` directly for the test instead of using `CycleNodes`!
            # The test is testing `architect_session_node`, which is a method on `ArchitectNodes`.
            from src.nodes.architect import ArchitectNodes
            architect_node = ArchitectNodes(jules=mock_jules, git=mock_git_instance)

            # Create state with requested_cycle_count
            state = CycleState(cycle_id="00")
            state.requested_cycle_count = 5

            # Execute the node
            await architect_node(state)

            # Verify run_session was called
            assert mock_jules.run_session.called

            # Get the actual prompt argument passed to run_session
            call_args = mock_jules.run_session.call_args
            actual_prompt = call_args.kwargs["prompt"]

            # Verify the constraint was injected
            assert "IMPORTANT CONSTRAINT" in actual_prompt
            assert "exactly 5 implementation cycles" in actual_prompt
            assert instruction_content in actual_prompt

    @pytest.mark.asyncio
    async def test_prompt_no_injection_without_count(self, tmp_path: Any) -> None:
        """Test that architect_session_node does NOT inject constraint when count is not specified."""
        # Setup mocks
        MagicMock()
        mock_jules = AsyncMock()
        mock_jules.run_session = AsyncMock(return_value={"status": "success"})

        # Create a temporary instruction file
        instruction_content = "Original architect instruction."

        # Mock settings.get_template to return our test content
        with (
            patch("src.nodes.architect.settings") as mock_settings,
            patch("src.services.git_ops.GitManager") as mock_git_cls,
            patch("src.nodes.architect.ProjectManager"),
        ):
            # Configure GitManager mock instance
            mock_git_instance = mock_git_cls.return_value
            mock_git_instance.create_feature_branch = AsyncMock()
            mock_git_instance.merge_pr = AsyncMock()

            mock_template = MagicMock()
            mock_template.read_text.return_value = instruction_content
            mock_settings.get_template.return_value = mock_template
            mock_settings.get_context_files.return_value = []

            from src.nodes.architect import ArchitectNodes
            architect_node = ArchitectNodes(jules=mock_jules, git=mock_git_instance)

            # Create state WITHOUT requested_cycle_count
            # BUT: CycleState defaults planned_cycle_count to 5 (from definition in state.py)
            # So if we want NO injection, we must explicitly set planned_cycle_count to None if allowed
            # or check that it uses planned_cycle_count logic.
            # In updated graph_nodes.py logic:
            # if requested_cycle_count: use it
            # elif planned_cycle_count: use it

            # If we want to test "no constraint", we need both to be None.
            state = CycleState(cycle_id="00")
            state.requested_cycle_count = None
            state.planned_cycle_count = None

            # Execute the node
            await architect_node(state)

            # Verify run_session was called
            assert mock_jules.run_session.called

            # Get the actual prompt argument passed to run_session
            call_args = mock_jules.run_session.call_args
            actual_prompt = call_args.kwargs["prompt"]

            # Verify the constraint was NOT injected
            assert "IMPORTANT CONSTRAINT" not in actual_prompt
            assert "implementation cycles" not in actual_prompt
            assert actual_prompt == instruction_content

    @pytest.mark.parametrize("count_value", [1, 2, 3, 5, 10])
    @pytest.mark.asyncio
    async def test_prompt_injection_various_counts(self, count_value: int) -> None:
        """Test that the correct count value is injected for various inputs."""
        # Setup mocks
        MagicMock()
        mock_jules = AsyncMock()
        mock_jules.run_session = AsyncMock(return_value={"status": "success"})

        instruction_content = "Test instruction."

        with (
            patch("src.nodes.architect.settings") as mock_settings,
            patch("src.services.git_ops.GitManager") as mock_git_cls,
            patch("src.nodes.architect.ProjectManager"),
        ):
            # Configure GitManager mock instance
            mock_git_instance = mock_git_cls.return_value
            mock_git_instance.create_feature_branch = AsyncMock()
            mock_git_instance.merge_pr = AsyncMock()

            mock_template = MagicMock()
            mock_template.read_text.return_value = instruction_content
            mock_settings.get_template.return_value = mock_template
            mock_settings.get_context_files.return_value = []

            from src.nodes.architect import ArchitectNodes
            architect_node = ArchitectNodes(jules=mock_jules, git=mock_git_instance)

            state = CycleState(cycle_id="00")
            state.requested_cycle_count = count_value

            await architect_node(state)

            call_args = mock_jules.run_session.call_args
            actual_prompt = call_args.kwargs["prompt"]

            # Verify the specific count is in the prompt
            assert f"exactly {count_value} implementation cycles" in actual_prompt
