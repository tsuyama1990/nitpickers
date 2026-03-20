import re


def sanitize_for_llm(content: str, max_length: int = 100000) -> str:
    """
    Sanitizes arbitrary text before inclusion in LLM prompts.
    Escapes dangerous markdown blocks to prevent prompt injection
    and truncates to avoid token limits or overwhelming context.

    Only allows basic printable text characters, newlines, and common symbols.
    Filters out invisible control characters that might be used maliciously.
    """
    if not content:
        return ""

    # Truncate string to max length
    truncated = content[:max_length]

    # Escape markdown code blocks to prevent premature prompt closure
    escaped = truncated.replace("```", "\\`\\`\\`")

    # Remove potentially dangerous ANSI escape codes and invisible control chars
    # Allow newlines (\n, \r), tabs (\t)
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    no_ansi = ansi_escape.sub("", escaped)

    # Filter non-printable characters except standard whitespaces
    # \x20-\x7E covers printable ASCII, \t\n\r covers standard whitespace
    # We also strip low ascii controls and dangerous unicode controls (\x7f-\x9f)
    control_chars = re.compile(r"[\x00-\x08\x0b\x0c\x0e\x0f\x10-\x19\x1a-\x1f\x7f-\x9f]")

    # Also strip unicode formatting characters that could be used for invisible prompt injection
    # e.g., zero-width spaces, directional formatting
    unicode_controls = re.compile(r"[\u200B-\u200D\uFEFF\u200E\u200F\u202A-\u202E]")

    safe_text = control_chars.sub("", no_ansi)
    safe_text = unicode_controls.sub("", safe_text)

    return str(safe_text)
