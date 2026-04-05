import asyncio

from rich.console import Console

from src.config import settings
from src.services.jules.api import JulesApiClient

console = Console()


async def main() -> None:
    client = JulesApiClient(settings.JULES_API_KEY.get_secret_value())
    activities = await client.list_activities_async("sessions/2654859668936207444")
    if activities:
        console.print(activities[-1])
    else:
        console.print("No activities found")


if __name__ == "__main__":
    asyncio.run(main())
