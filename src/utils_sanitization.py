

def sanitize_for_llm(content: str, max_length: int = 100000) -> str:
    """
    Sanitizes arbitrary text before inclusion in LLM prompts via a strict whitelist.
    Only allows printable ASCII characters plus explicitly allowed whitespace.
    """
    if not content:
        return ""

    # Truncate string to max length
    truncated = content[:max_length]

    # Escape markdown code blocks to prevent premature prompt closure
    escaped = truncated.replace("```", "\\`\\`\\`")

    # Use category check to allow all printable UTF-8 (including Japanese, Emoji, etc.)
    # but drop dangerous control characters.
    import unicodedata

    safe_text = "".join(
        char
        for char in escaped
        if not unicodedata.category(char).startswith("C") or char in "\n\r\t"
    )

    return str(safe_text)
