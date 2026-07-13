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
) -> tuple[list[TranscriptSegment], str]:
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    raw_segments, info = model.transcribe(
        str(media_path), language=None, beam_size=5, vad_filter=True, condition_on_previous_text=True
    )
    segments: list[TranscriptSegment] = []
    for item in raw_segments:
        text = item.text.strip()
        if text:
            segments.append(TranscriptSegment(float(item.start), float(item.end), text))
        if progress:
            progress("Transcribing audio", min(1.0, item.end / duration) if duration else None)
    return segments, info.language


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
        segments, language = _run(media_path, model_name, device, compute_type, duration, progress)
        return segments, language, device
    except RuntimeError as error:
        message = str(error).lower()
        cuda_failure = device == "cuda" and any(term in message for term in ("cuda", "cublas", "cudnn", ".dll"))
        if not cuda_failure or not fallback_to_cpu:
            raise
        if progress:
            progress("GPU libraries unavailable; retrying with CPU", None)
        segments, language = _run(media_path, model_name, "cpu", "int8", duration, progress)
        return segments, language, "cpu-fallback"
