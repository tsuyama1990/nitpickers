
from src.utils_sanitization import sanitize_for_llm


def test_sanitize_empty_string() -> None:
    assert sanitize_for_llm("") == ""
    assert sanitize_for_llm(None) == ""  # type: ignore[arg-type]


def test_sanitize_normal_text() -> None:
    text = "Hello World! 123 \n\t\r"
    assert sanitize_for_llm(text) == text


def test_sanitize_truncation() -> None:
    text = "abcdefghij"
    assert sanitize_for_llm(text, max_length=5) == "abcde"
    assert sanitize_for_llm(text, max_length=10) == "abcdefghij"
    assert sanitize_for_llm(text, max_length=15) == "abcdefghij"


def test_sanitize_markdown_code_blocks() -> None:
    text = "Here is some code:\n```python\nprint('hello')\n```"
    expected = "Here is some code:\n\\`\\`\\`python\nprint('hello')\n\\`\\`\\`"
    assert sanitize_for_llm(text) == expected


def test_sanitize_drops_ansi_and_unprintable() -> None:
    # Text with ANSI escape codes
    text = "\x1b[31mRed Text\x1b[0m and normal text"
    # The whitelist logic will drop the '\x1b' (escape character) because it's not in string.printable
    # So it becomes "[31mRed Text[0m and normal text"
    expected = "[31mRed Text[0m and normal text"
    assert sanitize_for_llm(text) == expected

    # Text with zero-width space (U+200B) and other non-ascii
    text_non_ascii = "Hello\u200bWorld \u2603"
    assert sanitize_for_llm(text_non_ascii) == "HelloWorld "


def test_sanitize_drops_vertical_tab_and_form_feed() -> None:
    text = "Line 1\x0bLine 2\x0cLine 3"
    assert sanitize_for_llm(text) == "Line 1Line 2Line 3"
