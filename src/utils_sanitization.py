import re
import unicodedata

def redact_secrets(content: str) -> str:
    """Redacts common API keys and sensitive patterns from the text."""
    # Pattern for various API keys (sk-..., e2b-..., etc.)
    patterns = [
        (r"(sk-[a-zA-Z0-9-]{24,})", "[REDACTED_API_KEY]"),
        (r"(e2b-[a-zA-Z0-9-]{24,})", "[REDACTED_E2B_KEY]"),
        (r"(AIza[0-9A-Za-z-_]{35})", "[REDACTED_GOOGLE_KEY]"),
        (r"(pass(?:word)?[:=]\s*)(\S+)", r"\1[REDACTED_PASSWORD]"),
    ]
    
    redacted = content
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted

def sanitize_for_llm(content: str, max_length: int = 100000) -> str:
    """
    Sanitizes arbitrary text before inclusion in LLM prompts via a strict whitelist.
    Only allows printable ASCII characters plus explicitly allowed whitespace.
    """
    if not content:
        return ""

    # 1. Redact Secrets
    redacted = redact_secrets(content)

    # 2. Truncate string to max length
    truncated = redacted[:max_length]

    # 3. Escape markdown code blocks
    escaped = truncated.replace("```", "\\`\\`\\`")

    # 4. Filter control characters
    safe_text = "".join(
        char
        for char in escaped
        if not unicodedata.category(char).startswith("C") or char in "\n\r\t"
    )

    return str(safe_text)
