from pathlib import Path

from videonote.config import Settings
from videonote.models import TranscriptSegment, VideoInfo
from videonote.pipeline import PipelineOptions, run_pipeline


def test_pipeline_with_subtitles_and_mocked_llm(monkeypatch, tmp_path):
    video = VideoInfo(
        url="https://example.com/video", video_id="v1", title="Test Video",
        platform="youtube", duration=10, webpage_url="https://example.com/video",
    )
    subtitle_path = tmp_path / "source.vtt"
    subtitle_path.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:04.000\nTechnical content for testing.\n", encoding="utf-8")

    monkeypatch.setattr("videonote.pipeline.get_video_info", lambda *args: (video, {"subtitles": {"en": [{}]}}))
    monkeypatch.setattr("videonote.pipeline.download_subtitle", lambda *args: (subtitle_path, "en", "manual_subtitle"))
    monkeypatch.setattr("videonote.pipeline.chunks_as_context", lambda chunks, client, max_chars: "[00:00] Technical content")
    monkeypatch.setattr("videonote.pipeline.plan_note", lambda *args: {"title": "Test Note", "sections": {}})
    note = """---
title: Test Note
source: https://example.com/video
platform: youtube
source_language: en
note_language: zh-TW
created: 2026-07-14
tags: [test]
---

# Test Note

## Summary

Technical content.
"""
    monkeypatch.setattr("videonote.pipeline.generate_note", lambda *args: note)
    monkeypatch.setattr("videonote.pipeline.repair_note", lambda *args: note)
    monkeypatch.setattr("videonote.pipeline.validate_grounding", lambda *args: {
        "supported_claims": ["Technical content"], "unsupported_claims": [],
        "missing_key_points": [], "possible_transcription_errors": [], "overall_score": 95,
    })

    events = []
    result = run_pipeline(
        PipelineOptions(url=video.url), tmp_path / "job",
        lambda stage, progress, message: events.append((stage, progress)),
        Settings(
            tmp_path / "data", "test", "test-model", "https://example.com/api/v1",
            "http://localhost", "VideoNote Test", 1000,
        ),
    )

    assert result.markdown == note
    assert result.transcript["source"] == "manual_subtitle"
    assert result.validation["passed"] is True
    assert Path(result.files["markdown"]).exists()
    assert events[-1] == ("complete", 100)
