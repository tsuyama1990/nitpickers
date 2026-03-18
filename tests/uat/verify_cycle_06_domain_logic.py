import marimo

__generated_with = "0.10.14"
app = marimo.App()


@app.cell
def _imports():
    import subprocess
    import sys
    from pathlib import Path

    import marimo as mo

    from src.services.conflict_manager import ConflictManager, ConflictMarkerRemainsError
    from src.services.git_ops import GitManager

    manager = ConflictManager()

    return (
        ConflictManager,
        ConflictMarkerRemainsError,
        GitManager,
        Path,
        manager,
        mo,
        subprocess,
        sys,
    )


@app.cell
def _markdown(manager, mo, path_mod):
    mo.md(
        """
        # CYCLE 06 UAT: Conflict Extraction & Registry Management

        This script validates the scenarios defined in `UAT.md`.
        """
    )


@app.cell
def _logic(git_mgr_cls, manager, path_mod, conflict_err_cls, subprocess):  # noqa: PLR0915
    async def run_scenarios():  # noqa: PLR0915
        # Setup temporary git repo
        test_dir = path_mod("uat_test_repo")
        if test_dir.exists():
            import shutil

            shutil.rmtree(test_dir)

        test_dir.mkdir()

        def run_git(*args):
            return subprocess.run(
                ["git", *args],
                cwd=test_dir,
                capture_output=True,
                text=True,
                check=False,
            )

        run_git("init")
        run_git("config", "user.name", "UAT User")
        run_git("config", "user.email", "uat@example.com")

        # Initial commit on main
        test_file = test_dir / "test_file.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3\n")
        run_git("add", "test_file.txt")
        run_git("commit", "-m", "Initial commit")

        # Branch feature/A
        run_git("checkout", "-b", "feature/A")
        test_file.write_text("Line 1 Modified\nLine 2\nLine 3\n")
        run_git("add", "test_file.txt")
        run_git("commit", "-m", "Feature A changes")

        # Back to main, create branch feature/B
        run_git("checkout", "main")
        run_git("checkout", "-b", "feature/B")
        test_file.write_text("Line 1\nLine 2\nLine 3 Modified\n")
        run_git("add", "test_file.txt")
        run_git("commit", "-m", "Feature B changes")

        # Scenario 06-01: Successful Clean Merge
        # Merging feature/A into feature/B should be clean

        # Scenario 06-02: Conflict Extraction
        run_git("checkout", "main")
        run_git("checkout", "-b", "conflict_A")
        test_file.write_text("Conflict Line A\nLine 2\nLine 3\n")
        run_git("add", "test_file.txt")
        run_git("commit", "-m", "Conflict A")

        run_git("checkout", "main")
        run_git("checkout", "-b", "conflict_B")
        test_file.write_text("Conflict Line B\nLine 2\nLine 3\n")
        run_git("add", "test_file.txt")
        run_git("commit", "-m", "Conflict B")

        # Create conflict
        res = run_git("merge", "--no-commit", "--no-ff", "conflict_A")
        if res.returncode == 0:
            msg = "Merge should fail"
            raise AssertionError(msg)

        items = manager.scan_conflicts(test_dir)
        if len(items) != 1:
            msg = "Should find 1 conflict"
            raise AssertionError(msg)

        if items[0].file_path != "test_file.txt":
            msg = "Incorrect conflict file path"
            raise AssertionError(msg)

        if len(items[0].conflict_markers) < 3:
            msg = "Should have conflict markers"
            raise AssertionError(msg)

        # Scenario 06-03: Resolution Validation Failsafe
        try:
            manager.validate_resolution(test_file)
            msg = "Should have raised exception"
            raise AssertionError(msg)
        except conflict_err_cls:
            pass  # Validation Failsafe triggered correctly on conflicted file.

        # Resolve it manually
        test_file.write_text("Resolved Line\nLine 2\nLine 3\n")
        if manager.validate_resolution(test_file) is not True:
            msg = "Should pass on clean file"
            raise AssertionError(msg)

    return run_scenarios,


@app.cell
def _runner(run_scenarios):
    import asyncio

    asyncio.run(run_scenarios())


if __name__ == "__main__":
    app.run()
