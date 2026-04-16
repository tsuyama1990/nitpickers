import asyncio
import os
import sys

# Ensure src module can be found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.llm_reviewer import LLMReviewer


async def main():
    reviewer = LLMReviewer()

    # Simple target and context to avoid long generation
    target_files = {"test_target.py": "def add(a, b):\n    return a + b"}
    context_docs = {
        "test_context.md": "# Specification\nThe code should perform addition properly."
    }
    instruction = "Please review this code according to the specification."
    model = "openrouter/arcee-ai/trinity-large-preview:free"

    print(f"Testing LLMReviewer.review_code with model: {model}")
    print("Sending API request...")

    try:
        result = await reviewer.review_code(
            target_files=target_files,
            context_docs=context_docs,
            instruction=instruction,
            model=model,
        )
        print("\n=== SUCCESS ===")
        print(result)
    except Exception as e:
        print("\n=== EXCEPTION CAUGHT ===")
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
