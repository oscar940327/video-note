from videonote.note_validator import annotate_review_items, format_validation


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


def test_review_items_are_written_into_markdown_once():
    validation = {
        "passed": True,
        "errors": [],
        "warnings": [],
        "grounding": {
            "unsupported_claims": ["〈Summary〉「Technical content」— transcript does not support this detail"],
            "missing_key_points": ["[00:00:03] Missing deployment warning"],
            "possible_transcription_errors": ["[00:00:02] \"agent\" — may be \"agents\""],
        },
    }

    annotated = annotate_review_items(VALID_NOTE, validation)
    assert "[!warning] 需要人工檢查" in annotated
    assert "〈Summary〉「Technical content」" in annotated
    assert "[00:00:02]" in annotated
    assert annotated.index("需要人工檢查") < annotated.index("# Test")

    updated = annotate_review_items(annotated, validation)
    assert updated.count("VIDEONOTE_REVIEW_START") == 1
    assert format_validation(updated)["passed"] is True
