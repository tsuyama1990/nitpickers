import json
import os
import subprocess
from pathlib import Path


def get_coverage(ignore_file: str | None = None) -> str:
    cwd = Path("/home/tomo/project/nitpickers")
    venv_pytest = cwd / ".venv" / "bin" / "pytest"
    cmd = [str(venv_pytest), "tests/", "--cov=src", "--cov-report=json"]

    cmd.extend(
        [
            "--ignore=tests/nitpick/unit/test_workflow_orchestration.py",
            "--ignore=tests/integration/test_tracing_integration.py",
            "--ignore=tests/nitpick/unit/test_jules_client_logic.py",
        ]
    )

    if ignore_file:
        cmd.append(f"--ignore={ignore_file}")

    env = os.environ.copy()
    env.update({"OPENROUTER_API_KEY": "test", "JULES_API_KEY": "test", "E2B_API_KEY": "test"})

    subprocess.run(  # noqa: S603
        cmd,
        env=env,
        cwd=str(cwd),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )

    with (cwd / "coverage.json").open() as f:
        data = json.load(f)
        return str(data["totals"]["percent_covered_display"])


print("Getting baseline coverage...")  # noqa: T201
baseline = float(get_coverage())
print(f"Baseline coverage: {baseline}%")  # noqa: T201

integration_tests = list(Path("tests/nitpick/integration").glob("*.py")) + list(
    Path("tests/integration").glob("*.py")
)

print("Checking tests for redundancy...")  # noqa: T201
for test_file in integration_tests:
    if "test_tracing_integration" in str(test_file):
        continue
    cov = float(get_coverage(str(test_file)))
    diff = baseline - cov
    if diff <= 0.05:
        print(f"[REDUNDANT] {test_file} (Coverage drop: {diff:.2f}%)")  # noqa: T201
    else:
        print(f"[NEEDED] {test_file} (Coverage drop: {diff:.2f}%)")  # noqa: T201
