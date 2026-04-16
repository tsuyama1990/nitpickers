import asyncio
import os

from dotenv import load_dotenv
from openai import AsyncOpenAI


async def test_openrouter():
    # Load .env file
    load_dotenv()

    # --- MANUAL KEY OVERRIDE ---
    # You can paste your key here to test it directly.
    # If this is empty, it will use the one from .env
    MANUAL_KEY = ""

    api_key = MANUAL_KEY or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ Error: OPENROUTER_API_KEY not found in .env file or environment.")
        return

    print(
        f"Checking connection with key: {api_key[:5]}...{api_key[-5:] if len(api_key) > 5 else ''}"
    )

    # --- MANUAL MODEL OVERRIDE ---
    MANUAL_MODEL = "openrouter/arcee-ai/trinity-large-preview:free"
    model = MANUAL_MODEL

    # Initialize OpenAI client for OpenRouter
    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    try:
        print(f"Sending 'Hello' to model {model} via OpenRouter...")
        # Note: OpenRouter doesn't always need the 'openrouter/' prefix for the model name
        # when using their base_url, but it depends on how it's being routed.
        # We'll try with the full name first.

        response = await client.chat.completions.create(
            model=model.replace("openrouter/", ""),  # OpenRouter model ID
            messages=[
                {
                    "role": "user",
                    "content": "Hello! Please reply with 'Hello from OpenRouter!' if you can hear me.",
                }
            ],
            temperature=0.7,
        )
        content = response.choices[0].message.content
        print(f"\n✅ Success! Response from LLM:\n{content}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if "401" in str(e):
            print("This usually means your API key is invalid.")


if __name__ == "__main__":
    asyncio.run(test_openrouter())
