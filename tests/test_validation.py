from videonote.note_validator import format_validation


VALID_NOTE = """---
title: Test
source: https://example.com
platform: youtube
source_language: en
note_language: zh-TW
created: 2026-07-14
tags: [test]
---

# Test

## Summary

Content.

```python
print("ok")
```
"""


def test_valid_markdown_passes():
    result = format_validation(VALID_NOTE)
    assert result["passed"] is True
    assert result["errors"] == []


def test_unbalanced_fence_fails():
    result = format_validation(VALID_NOTE + "\n```text\nmissing close")
    assert result["passed"] is False
    assert "Code fences are not balanced." in result["errors"]


def test_duplicate_heading_warns():
    result = format_validation(VALID_NOTE + "\n## Summary\n\nAgain.\n")
    assert any("Duplicate headings" in warning for warning in result["warnings"])
