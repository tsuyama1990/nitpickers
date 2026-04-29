import os
from datetime import UTC, datetime, timedelta

from langsmith import Client


def check_recent_traces() -> None:
    client = Client()

    # Get recent runs from the last 24 hours
    start_time = datetime.now(UTC) - timedelta(hours=24)

    print(f"--- Fetching recent runs since {start_time} (UTC) ---")  # noqa: T201

    potential_projects = [
        os.environ.get("LANGCHAIN_PROJECT"),
        "nitpickers-default",
        "nitpickers_from_desktop",
        "nitpickers",
    ]

    runs = []
    for proj in potential_projects:
        if not proj:
            continue
        print(f"--- Attempting to fetch runs from Project: {proj} ---")  # noqa: T201
        try:
            runs = list(client.list_runs(project_name=proj, start_time=start_time, limit=5))
            if runs:
                print(f"Successfully found {len(runs)} runs in {proj}")  # noqa: T201
                break
        except Exception as e:
            print(f"Skipping {proj}: {e}")  # noqa: T201

    if not runs:
        print("No recent runs found in any potential LangSmith project.")  # noqa: T201
        return

    for run in runs:
        print(f"\nRun ID: {run.id}")  # noqa: T201
        print(f"Name: {run.name}")  # noqa: T201
        print(f"Status: {run.status}")  # noqa: T201
        print(f"Start Time: {run.start_time}")  # noqa: T201
        if run.error:
            print(f"Error: {run.error}")  # noqa: T201

        # List child runs (nodes)
        child_runs = list(client.list_runs(parent_run_id=run.id))
        if child_runs:
            print("Node Transitions:")  # noqa: T201
            for child in sorted(child_runs, key=lambda x: x.start_time):
                print(f"  -> {child.name} ({child.status})")  # noqa: T201


if __name__ == "__main__":
    check_recent_traces()
