import os
import pwd
import typing
from pathlib import Path

from src.utils import logger


class PermissionManager:
    """Manages file permissions and ownership."""

    async def fix_permissions(self, *paths: Path) -> None:  # noqa: PLR0912, PLR0915
        """Fix file ownership to current user if created with elevated privileges."""
        uid: int | None = None
        gid: int | None = None
        target_user: str | None = None

        if "HOST_UID" in os.environ and "HOST_GID" in os.environ:
            try:
                uid = int(os.environ["HOST_UID"])
                gid = int(os.environ["HOST_GID"])
                target_user = f"host user (UID={uid})"
                logger.info(f"Detected Docker environment: HOST_UID={uid}, HOST_GID={gid}")
            except ValueError:
                logger.debug("Invalid HOST_UID/HOST_GID values")

        if uid is None and "SUDO_USER" in os.environ:
            actual_user = os.environ["SUDO_USER"]
            try:
                pw_record = pwd.getpwnam(actual_user)
                uid = pw_record.pw_uid
                gid = pw_record.pw_gid
                target_user = actual_user
                logger.info(f"Detected sudo environment: user={actual_user}")
            except KeyError:
                logger.debug(f"User {actual_user} not found")

        if uid is None:
            current_user = os.environ.get("USER")
            if current_user and current_user != "root":
                try:
                    pw_record = pwd.getpwnam(current_user)
                    uid = pw_record.pw_uid
                    gid = pw_record.pw_gid
                    target_user = current_user
                except KeyError:
                    pass

        def _walk(p: str) -> typing.Iterator[tuple[str, bool]]:
            yield p, Path(p).is_dir()
            try:
                for entry in os.scandir(p):
                    try:
                        is_dir_no_sym = entry.is_dir(follow_symlinks=False)
                        is_dir_with_sym = entry.is_dir(follow_symlinks=True)
                    except OSError:
                        continue
                    if is_dir_no_sym:
                        yield from _walk(entry.path)
                    else:
                        yield entry.path, is_dir_with_sym
            except (PermissionError, OSError):
                pass

        if uid is not None and gid is not None and uid != 0:
            try:
                for path in paths:
                    if path.exists():
                        for item_path, _ in _walk(str(path)):
                            try:
                                os.chown(item_path, uid, gid)
                            except (PermissionError, OSError) as e:
                                logger.debug(f"Could not fix ownership for {item_path}: {e}")
                logger.info(f"✓ Fixed file ownership for {target_user}")
            except Exception as e:
                logger.debug(f"Could not chown: {e}")

        try:
            for path in paths:
                if path.exists():
                    for item_path, is_dir in _walk(str(path)):
                        try:
                            if is_dir:
                                os.chmod(item_path, 0o777)  # noqa: S103, PTH101
                            else:
                                os.chmod(item_path, 0o666)  # noqa: S103, PTH101
                        except (PermissionError, OSError) as e:
                            logger.debug(f"Could not relax permissions for {item_path}: {e}")
            logger.debug("✓ Set permissive file permissions (rw-rw-rw-)")
        except Exception as e:
            logger.debug(f"Could not fix permissions via chmod: {e}")
