import re
from pathlib import Path

from src.domain_models.execution import ConflictRegistryItem
from src.utils import logger


class ConflictMarkerRemainsError(Exception):
    """Raised when a file still contains Git conflict markers."""


class ConflictManager:
    """Extracts and validates Git conflict markers."""

    def __init__(self) -> None:
        self.conflict_marker_pattern = re.compile(r"^(<{7}\s.*|={7}|>{7}\s.*)$", re.MULTILINE)

    def scan_conflicts(self, repo_path: Path) -> list[ConflictRegistryItem]:
        """
        Scans the repository for files with standard git conflict markers and
        returns a list of ConflictRegistryItem objects representing them.
        """
        import subprocess

        try:
            from src.config import settings

            git_cmd = settings.tools.git_cmd

            # Use git status --porcelain to find unmerged files quickly
            result = subprocess.run(  # noqa: S603
                [git_cmd, "status", "--porcelain"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as e:
            logger.error(f"Error scanning for conflicts: {e}")
            return []

        unmerged_files = []
        if result.stdout:
            conflict_codes = settings.tools.conflict_codes
            for line in result.stdout.splitlines():
                if len(line) >= 3 and line[:2] in conflict_codes:
                    unmerged_files.append(line[3:])

        registry_items = []
        for file_path_str in unmerged_files:
            file_path = repo_path / file_path_str
            if not file_path.exists() or not file_path.is_file():
                continue

            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue  # Skip binary files
            except (FileNotFoundError, PermissionError) as e:
                logger.warning(f"Could not read {file_path} during conflict scan: {e}")
                continue

            markers = self.conflict_marker_pattern.findall(content)
            if markers:
                registry_items.append(
                    ConflictRegistryItem(
                        file_path=file_path_str,
                        conflict_markers=markers,
                    )
                )

        return registry_items

    def validate_resolution(self, file_path: Path) -> bool:
        """
        Reads the given file and returns False if any standard git conflict
        markers remain.
        """
        if not file_path.exists() or not file_path.is_file():
            return True

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return True  # Binary files handled differently, assume True for text based check
        except (FileNotFoundError, PermissionError) as e:
            logger.warning(f"Could not read {file_path} during conflict validation: {e}")
            return True

        if self.conflict_marker_pattern.search(content):
            err_msg = f"File {file_path} still contains git conflict markers."
            raise ConflictMarkerRemainsError(err_msg)

        return True

    def build_conflict_package(self, item: ConflictRegistryItem, repo_path: Path) -> str:
        """
        Builds the conflict resolution prompt package for the Jules Master Integrator session.
        Extracts Base, Local (Branch A), and Remote (Branch B) versions using Git 3-Way Diff.
        """
        import subprocess

        try:
            from src.config import settings

            git_cmd = settings.tools.git_cmd
        except Exception:
            git_cmd = "git"

        def _get_git_version(stage: int) -> str:
            try:
                result = subprocess.run(  # noqa: S603
                    [git_cmd, "show", f":{stage}:{item.file_path}"],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    check=True,
                )
                return result.stdout.strip()
            except subprocess.CalledProcessError:
                return "<FILE_NOT_IN_BASE>" if stage == 1 else ""

        base_code = _get_git_version(1)
        local_code = _get_git_version(2)
        remote_code = _get_git_version(3)

        # Read specific instructions from MASTER_INTEGRATOR_PROMPT.md if available
        try:
            from src.config import settings

            prompt_template = settings.get_prompt_content("MASTER_INTEGRATOR_PROMPT.md")
        except Exception:
            prompt_template = ""

        if not prompt_template:
            prompt_template = (
                "You are the Master Integrator. Resolve the Git conflicts in this file.\n"
                "Do not just pick A or B; understand the intent of both branches.\n"
                "Apply DRY principles. Return the completely unified file without any `<<<<<<<` markers.\n"
                "Respond ONLY with the strictly validated JSON schema requested."
            )

        return f"""{prompt_template}

###################
File: {item.file_path}

### Base (元のコード)
```python
{base_code}
```

### Branch A の変更 (Local)
```python
{local_code}
```

### Branch B の変更 (Remote)
```python
{remote_code}
```
"""
