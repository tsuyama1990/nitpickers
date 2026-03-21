import shutil
import time
from pathlib import Path

from src.services.file_ops import FilePatcher


def setup_dummy_files(num_files: int = 50000, lines_per_file: int = 100, dest_dir: str = "dummy_src") -> None:
    path = Path(dest_dir)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir()

    content = "This is a dummy line.\n" * lines_per_file

    for i in range(num_files):
        (path / f"file_{i}.py").write_text(content, encoding="utf-8")

def main() -> None:
    dest_dir = "dummy_src"
    setup_dummy_files()

    patcher = FilePatcher()

    start_time = time.time()
    result = patcher.read_src_files(dest_dir)
    end_time = time.time()

    duration = end_time - start_time

    # Cleanup
    shutil.rmtree(dest_dir)

if __name__ == "__main__":
    main()
