import shutil
import time
from pathlib import Path

from src.services.file_ops import FilePatcher


def setup_dummy_files(num_files=50000, lines_per_file=100, dest_dir="dummy_src"):
    path = Path(dest_dir)
    if path.exists():
        shutil.rmtree(path)
    path.mkdir()

    content = "This is a dummy line.\n" * lines_per_file

    for i in range(num_files):
        (path / f"file_{i}.py").write_text(content, encoding="utf-8")

def main():
    dest_dir = "dummy_src"
    print("Setting up dummy files...")
    setup_dummy_files()

    patcher = FilePatcher()

    print("Running read_src_files benchmark...")
    start_time = time.time()
    result = patcher.read_src_files(dest_dir)
    end_time = time.time()

    duration = end_time - start_time
    print(f"Time taken: {duration:.4f} seconds")
    print(f"Total size read: {len(result) / (1024*1024):.2f} MB")

    # Cleanup
    shutil.rmtree(dest_dir)

if __name__ == "__main__":
    main()
