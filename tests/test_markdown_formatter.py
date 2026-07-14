from videonote.markdown_formatter import normalize_markdown
from videonote.models import VideoInfo
from videonote.note_validator import format_validation


def test_normalize_markdown_repairs_deterministic_structure():
    video = VideoInfo(
        url="https://example.com/v", video_id="v", title="Test", platform="youtube",
        webpage_url="https://example.com/v",
    )
    markdown = (
        "# Test\n\n### Jumped\n\nContent.\n\n## Empty\n\n"
        "## Code\n\n```python\nprint('x')\n"
    )

    result = normalize_markdown(
        markdown, video, {"title": "Test", "tags": ["ai"]}, "en", "zh-TW"
    )

    validation = format_validation(result)
    assert validation["passed"] is True
    assert "source: https://example.com/v" in result
    assert "## Jumped" in result
    assert "## Empty" not in result
    assert result.rstrip().endswith("```")
