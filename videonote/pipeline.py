from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .config import Settings, settings
from .llm_service import OpenRouterClient, chunks_as_context
from .models import Transcript
from .note_generator import generate_note, repair_note
from .note_planner import plan_note
from .note_validator import format_validation, validate_grounding
from .subtitle_service import download_subtitle, parse_subtitle
from .transcript_processor import chunk_segments, clean_segments
from .transcription_service import transcribe_audio
from .utils import atomic_write_text, safe_name, timestamp, write_json
from .video_service import download_audio, get_video_info, normalize_video_url


ProgressCallback = Callable[[str, int, str], None]


@dataclass
class PipelineOptions:
    url: str
    output_language: str = "zh-TW"
    whisper_model: str = "large-v3"
    note_style: str = "standard"
    grounding_mode: str = "assisted"
    force_cpu: bool = False
    cookies_from_browser: str | None = None


@dataclass
class PipelineResult:
    markdown: str
    video: dict
    transcript: dict
    plan: dict
    validation: dict
    files: dict[str, str]


def write_transcript_outputs(transcript: Transcript, directory: Path) -> dict[str, Path]:
    base = safe_name(transcript.video.title)
    txt_path = directory / f"{base}.txt"
    srt_path = directory / f"{base}.srt"
    json_path = directory / f"{base}.json"
    atomic_write_text(txt_path, transcript.text + "\n")
    srt_parts = []
    for index, segment in enumerate(transcript.segments, start=1):
        srt_parts.append(
            f"{index}\n{timestamp(segment.start, srt=True)} --> {timestamp(segment.end, srt=True)}\n{segment.text}\n"
        )
    atomic_write_text(srt_path, "\n".join(srt_parts))
    write_json(json_path, transcript.to_dict())
    return {"txt": txt_path, "srt": srt_path, "json": json_path}


def run_pipeline(
    options: PipelineOptions,
    job_dir: Path,
    progress: ProgressCallback,
    app_settings: Settings = settings,
) -> PipelineResult:
    job_dir.mkdir(parents=True, exist_ok=True)
    options.url = normalize_video_url(options.url)
    raw_dir = job_dir / "raw"
    raw_dir.mkdir(exist_ok=True)

    progress("video_info", 5, "Reading video information")
    video, raw_info = get_video_info(options.url, options.cookies_from_browser)
    effective_cookies = options.cookies_from_browser
    if raw_info.pop("_videonote_cookie_fallback", False):
        effective_cookies = None
        progress("video_info", 8, "Browser cookies are locked; continuing without cookies")
    write_json(job_dir / "video.json", video.to_dict())

    progress("subtitles", 12, "Looking for official subtitles")
    subtitle = download_subtitle(options.url, raw_info, raw_dir, effective_cookies)
    if subtitle:
        subtitle_path, language, source = subtitle
        segments = parse_subtitle(subtitle_path)
        if not segments:
            raise RuntimeError("A subtitle file was downloaded but no timed text could be parsed.")
        transcript_source = source
        device = "not_used"
    else:
        progress("audio_download", 18, "No subtitle found; downloading audio")
        audio_path = download_audio(
            options.url,
            raw_dir,
            effective_cookies,
            lambda message, ratio: progress("audio_download", 18 + int((ratio or 0) * 12), message),
        )
        progress("transcription", 31, "Transcribing audio with automatic language detection")
        segments, language, device = transcribe_audio(
            audio_path,
            model_name=options.whisper_model,
            force_cpu=options.force_cpu,
            duration=video.duration,
            progress=lambda message, ratio: progress("transcription", 31 + int((ratio or 0) * 24), message),
        )
        transcript_source = "whisper"

    raw_transcript = Transcript(video=video, language=language, source=transcript_source, segments=segments)
    write_json(job_dir / "transcript.raw.json", raw_transcript.to_dict())

    progress("processing", 57, "Cleaning and chunking transcript")
    cleaned_segments = clean_segments(segments)
    cleaned = Transcript(video=video, language=language, source=transcript_source, segments=cleaned_segments)
    transcript_files = write_transcript_outputs(cleaned, job_dir / "transcripts")
    chunks = chunk_segments(cleaned_segments)
    write_json(job_dir / "transcript.chunks.json", [chunk.to_dict() for chunk in chunks])

    client = OpenRouterClient(app_settings)
    progress("context", 62, "Preparing transcript context")
    context = chunks_as_context(chunks, client, app_settings.max_llm_context_chars)
    atomic_write_text(job_dir / "transcript.context.txt", context)

    progress("planning", 69, "Planning note sections")
    plan = plan_note(client, video, context, options.output_language)
    write_json(job_dir / "note-plan.json", plan)

    progress("generation", 78, "Generating structured Markdown")
    markdown = generate_note(
        client, video, plan, context, options.output_language, options.note_style, options.grounding_mode
    )
    note_path = job_dir / f"{safe_name(plan.get('title') or video.title)}.md"
    atomic_write_text(note_path, markdown)

    progress("validation", 88, "Automatically repairing note issues")
    markdown = repair_note(client, markdown, context)
    atomic_write_text(note_path, markdown)

    progress("validation", 95, "Validating the repaired note")
    validation = format_validation(markdown)
    validation["grounding"] = validate_grounding(client, markdown, context)
    write_json(job_dir / "validation.json", validation)

    progress("complete", 100, "Note is ready for review")
    return PipelineResult(
        markdown=markdown,
        video=video.to_dict(),
        transcript={
            "language": language,
            "source": transcript_source,
            "segment_count": len(cleaned_segments),
            "device": device,
        },
        plan=plan,
        validation=validation,
        files={
            "markdown": str(note_path),
            **{name: str(path) for name, path in transcript_files.items()},
        },
    )
