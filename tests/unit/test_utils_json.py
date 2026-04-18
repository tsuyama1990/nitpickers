from src.utils_json import extract_json_from_text


def test_extract_json_skips_python_block() -> None:
    text = """
Here is the python fix:
```python
def foo():
    pass
```
And here is the JSON report:
```json
{
    "is_approved": false,
    "vulnerabilities": ["Critical bug in foo"]
}
```
"""
    result = extract_json_from_text(text)
    assert "Critical bug" in result
    assert "foo()" not in result


def test_extract_json_truncated() -> None:
    text = """
```json
{
    "is_approved": true,
    "reason": "Looking good
"""
    result = extract_json_from_text(text)
    assert result.endswith('Looking good"}')
    assert "is_approved" in result


def test_no_markdown_blocks_just_curly() -> None:
    text = """Some thoughts..
{
    "is_approved": true,
    "reason": "OK"
}
"""
    result = extract_json_from_text(text)
    assert "is_approved" in result
    assert "OK" in result
