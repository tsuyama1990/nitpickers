import re

for test_file in ["tests/unit/services/test_workflow.py", "tests/integration/test_pipeline_orchestration.py"]:
    with open(test_file, "r") as f:
        content = f.read()

    # Modify the successful pipeline tests to ensure they assert that the integration graph correctly received branches_to_merge
    # instead of just checking that it was called. The current implementation does `branches_to_merge.append(manifest.feature_branch)`
    # which is WRONG based on the spec, as it should be merging all cycle branches. So the test should assert it's merging all cycle branches.
    # Since we reverted workflow.py, this assertion will FAIL, giving us the required RED phase.

    if test_file == "tests/unit/services/test_workflow.py":
        search = """                        # Ensure all graphs were called
                        assert mock_integration_graph.ainvoke.call_count == 1"""

        replace = """                        # Ensure all graphs were called
                        assert mock_integration_graph.ainvoke.call_count == 1

                        # Verify the correct state was passed (TDD RED phase check)
                        state_arg = mock_integration_graph.ainvoke.call_args[0][0]
                        assert hasattr(state_arg, "branches_to_merge")
                        assert set(state_arg.branches_to_merge) == {"branch_1", "branch_2"}
"""
        content = content.replace(search, replace)
        with open(test_file, "w") as f:
            f.write(content)

    if test_file == "tests/integration/test_pipeline_orchestration.py":
        search = """                        assert "Full Pipeline Execution Completed Successfully" in result.stdout"""

        replace = """                        assert "Full Pipeline Execution Completed Successfully" in result.stdout

                        # Verify correct integration state (TDD RED phase check)
                        state_arg = mock_integration_graph.ainvoke.call_args[0][0]
                        assert set(state_arg.branches_to_merge) == {"branch_1", "branch_2"}
"""
        content = content.replace(search, replace)
        with open(test_file, "w") as f:
            f.write(content)
