import asyncio
import json

from rich.console import Console

from src.config import settings
from src.services.jules.api import JulesApiClient

console = Console()


async def main() -> None:
    client = JulesApiClient(settings.JULES_API_KEY.get_secret_value())
    session_id = "sessions/2654859668936207444"

    console.print(f"Checking session: {session_id}")
    activities = await client.list_activities_async(session_id)

    console.print(f"Total activities: {len(activities)}")
    for i, activity in enumerate(activities):
        console.print(f"\nActivity {i + 1}:")
        # Activity is a dict now (from list_activities_async)
        console.print(json.dumps(activity, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
