from pathlib import Path

import pytest

from videonote.models import TranscriptSegment
from videonote.transcription_service import _run_with_coverage_check, transcript_coverage


def test_short_transcript_retries_without_vad(monkeypatch):
    calls = []

    def fake_run(*args, vad_filter=True, **kwargs):
        calls.append(vad_filter)
        end = 140.0 if vad_filter else 1580.0
        return [TranscriptSegment(0, end, "content")], "zh"

    monkeypatch.setattr("videonote.transcription_service._run", fake_run)

    segments, language = _run_with_coverage_check(
        Path("audio.m4a"), "large-v3", "cpu", "int8", 1600.0, None
    )

    assert calls == [True, False]
    assert language == "zh"
    assert transcript_coverage(segments, 1600.0) == pytest.approx(0.9875)


def test_incomplete_retry_stops_before_llm_generation(monkeypatch):
    monkeypatch.setattr(
        "videonote.transcription_service._run",
        lambda *args, **kwargs: ([TranscriptSegment(0, 140, "partial")], "zh"),
    )

    with pytest.raises(RuntimeError, match="Transcription is incomplete"):
        _run_with_coverage_check(
            Path("audio.m4a"), "large-v3", "cpu", "int8", 1600.0, None
        )
