import asyncio
import json
from typing import Any

from rich.console import Console

from src.config import settings
from src.services.jules.api import JulesApiClient

console = Console()


async def extract_cycles(session_id: str) -> list[Any]:
    client = JulesApiClient(settings.JULES_API_KEY.get_secret_value())
    activities = await client.list_activities_async(session_id)

    # Look for planGenerated activity
    for activity in reversed(activities):
        if activity.get("type") == "planGenerated":
            return activity.get("plan", {}).get("cycles", [])  # type: ignore[no-any-return]

    # Fallback: look for agentMessaged with cycle info
    for activity in reversed(activities):
        if activity.get("type") == "agentMessaged":
            text = activity.get("message", {}).get("text", "")
            if "Cycle" in text and "Proposed Changes" in text:
                # This is harder to parse but we can try
                pass

    return []


if __name__ == "__main__":
    session_id = "sessions/17802859900124312593"
    cycles = asyncio.run(extract_cycles(session_id))
    console.print(json.dumps(cycles, indent=2))
