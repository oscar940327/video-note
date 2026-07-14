from __future__ import annotations

from pathlib import Path
from typing import Callable

import ctranslate2
from faster_whisper import WhisperModel

from .models import TranscriptSegment


ProgressCallback = Callable[[str, float | None], None]


def choose_device(force_cpu: bool) -> tuple[str, str]:
    if not force_cpu and ctranslate2.get_cuda_device_count() > 0:
        return "cuda", "float16"
    return "cpu", "int8"


def _run(
    media_path: Path,
    model_name: str,
    device: str,
    compute_type: str,
    duration: float | None,
    progress: ProgressCallback | None,
    vad_filter: bool = True,
) -> tuple[list[TranscriptSegment], str]:
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    raw_segments, info = model.transcribe(
        str(media_path), language=None, beam_size=5, vad_filter=vad_filter, condition_on_previous_text=True
    )
    segments: list[TranscriptSegment] = []
    for item in raw_segments:
        text = item.text.strip()
        if text:
            segments.append(TranscriptSegment(float(item.start), float(item.end), text))
        if progress:
            progress("Transcribing audio", min(1.0, item.end / duration) if duration else None)
    return segments, info.language


def transcript_coverage(segments: list[TranscriptSegment], duration: float | None) -> float | None:
    if not duration or duration <= 0 or not segments:
        return None
    return max(segment.end for segment in segments) / duration


def _coverage_is_suspicious(segments: list[TranscriptSegment], duration: float | None) -> bool:
    coverage = transcript_coverage(segments, duration)
    if coverage is None or duration is None or duration < 180:
        return False
    last_end = max(segment.end for segment in segments)
    return coverage < 0.65 and duration - last_end > 120


def _run_with_coverage_check(
    media_path: Path,
    model_name: str,
    device: str,
    compute_type: str,
    duration: float | None,
    progress: ProgressCallback | None,
) -> tuple[list[TranscriptSegment], str]:
    segments, language = _run(
        media_path, model_name, device, compute_type, duration, progress, vad_filter=True
    )
    if not _coverage_is_suspicious(segments, duration):
        return segments, language
    if progress:
        progress("Transcript ended far before the audio; retrying without VAD", None)
    segments, language = _run(
        media_path, model_name, device, compute_type, duration, progress, vad_filter=False
    )
    if _coverage_is_suspicious(segments, duration):
        coverage = transcript_coverage(segments, duration) or 0
        raise RuntimeError(
            f"Transcription is incomplete: only {coverage:.1%} of the video timeline was covered. "
            "The audio may be damaged or contain an unsupported discontinuity."
        )
    return segments, language


def transcribe_audio(
    media_path: Path,
    model_name: str = "large-v3",
    force_cpu: bool = False,
    duration: float | None = None,
    progress: ProgressCallback | None = None,
    fallback_to_cpu: bool = True,
) -> tuple[list[TranscriptSegment], str, str]:
    device, compute_type = choose_device(force_cpu)
    try:
        segments, language = _run_with_coverage_check(
            media_path, model_name, device, compute_type, duration, progress
        )
        return segments, language, device
    except RuntimeError as error:
        message = str(error).lower()
        cuda_failure = device == "cuda" and any(term in message for term in ("cuda", "cublas", "cudnn", ".dll"))
        if not cuda_failure or not fallback_to_cpu:
            raise
        if progress:
            progress("GPU libraries unavailable; retrying with CPU", None)
        segments, language = _run_with_coverage_check(
            media_path, model_name, "cpu", "int8", duration, progress
        )
        return segments, language, "cpu-fallback"
