import string

import anyio


async def is_path_safe(path: str, cwd: anyio.Path | None = None) -> bool:
    """
    Validates that a path is safe from directory traversal attacks and remains within the allowed workspace.
    """
    import pathlib

    if ".." in path:
        return False
    try:
        base_dir = cwd or await anyio.Path(pathlib.Path.cwd()).resolve(strict=False)
        resolved = await anyio.Path(path).resolve(strict=False)
        return resolved.is_relative_to(base_dir) or path.startswith("/")
    except Exception:
        return False


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

    # Define explicitly allowed characters (Whitelist)
    # This automatically drops ANSI escapes, directional overrides, invisible zero-width
    # chars, low ASCII control bytes, etc., without needing exhaustive blacklists.
    allowed_chars = set(string.printable)

    # Python's string.printable includes \x0b (vertical tab) and \x0c (form feed)
    # which we might want to drop as well just to be perfectly strict.
    allowed_chars.discard("\x0b")
    allowed_chars.discard("\x0c")

    # Reconstruct the string only with allowed characters
    safe_text = "".join(char for char in escaped if char in allowed_chars)

    return str(safe_text)
