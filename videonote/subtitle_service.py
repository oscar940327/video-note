from __future__ import annotations

import html
import json
import re
from pathlib import Path

from yt_dlp import YoutubeDL

from .models import TranscriptSegment, VideoInfo
from .video_service import ydl_options


LANGUAGE_PRIORITY = (
    "zh-Hant", "zh-TW", "zh-Hans", "zh-CN", "zh", "cmn-Hant", "cmn-Hans", "en", "en-US", "en-GB"
)


def choose_subtitle(info: dict) -> tuple[str, str] | None:
    manual = info.get("subtitles") or {}
    automatic = info.get("automatic_captions") or {}
    for source_name, source in (("manual_subtitle", manual), ("automatic_caption", automatic)):
        if not source:
            continue
        for language in LANGUAGE_PRIORITY:
            if language in source:
                return source_name, language
        return source_name, next(iter(source))
    return None


def download_subtitle(
    url: str,
    info: dict,
    destination: Path,
    cookies_from_browser: str | None = None,
) -> tuple[Path, str, str] | None:
    selected = choose_subtitle(info)
    if not selected:
        return None
    source, language = selected
    destination.mkdir(parents=True, exist_ok=True)
    options = ydl_options(cookies_from_browser)
    options.update({
        "skip_download": True,
        "writesubtitles": source == "manual_subtitle",
        "writeautomaticsub": source == "automatic_caption",
        "subtitleslangs": [language],
        "subtitlesformat": "vtt/srt/json3/best",
        "outtmpl": str(destination / "subtitle.%(ext)s"),
        "quiet": False,
    })
    before = set(destination.iterdir()) if destination.exists() else set()
    with YoutubeDL(options) as ydl:
        ydl.extract_info(url, download=True)
    candidates = [item for item in destination.iterdir() if item not in before and item.is_file()]
    if not candidates:
        candidates = list(destination.glob("subtitle*"))
    if not candidates:
        return None
    path = max(candidates, key=lambda item: item.stat().st_mtime)
    return path, language, source


def _parse_time(value: str) -> float:
    value = value.strip().replace(",", ".")
    parts = value.split(":")
    if len(parts) == 3:
        hours, minutes, seconds = parts
    else:
        hours, minutes, seconds = "0", parts[0], parts[1]
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def _clean_caption(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).replace("\u200b", "")
    return re.sub(r"\s+", " ", text).strip()


def parse_vtt_or_srt(content: str) -> list[TranscriptSegment]:
    segments: list[TranscriptSegment] = []
    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n"))
    time_pattern = re.compile(r"(?P<start>\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3})\s*-->\s*(?P<end>\d{1,2}:\d{2}(?::\d{2})?[.,]\d{3})")
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        timing_index = next((index for index, line in enumerate(lines) if "-->" in line), None)
        if timing_index is None:
            continue
        match = time_pattern.search(lines[timing_index])
        if not match:
            continue
        text = _clean_caption(" ".join(lines[timing_index + 1:]))
        if text:
            segments.append(TranscriptSegment(_parse_time(match["start"]), _parse_time(match["end"]), text))
    return segments


def parse_json_subtitle(content: str) -> list[TranscriptSegment]:
    data = json.loads(content)
    events = data.get("events") or data.get("body") or []
    segments: list[TranscriptSegment] = []
    for event in events:
        if "segs" in event:
            text = _clean_caption("".join(part.get("utf8", "") for part in event.get("segs", [])))
            start = float(event.get("tStartMs", 0)) / 1000
            end = start + float(event.get("dDurationMs", 0)) / 1000
        else:
            text = _clean_caption(str(event.get("content") or ""))
            start = float(event.get("from", 0))
            end = float(event.get("to", start))
        if text and text != "\n":
            segments.append(TranscriptSegment(start, end, text))
    return segments


def parse_subtitle(path: Path) -> list[TranscriptSegment]:
    content = path.read_text(encoding="utf-8-sig")
    if path.suffix.lower() in {".json", ".json3"} or content.lstrip().startswith("{"):
        return parse_json_subtitle(content)
    return parse_vtt_or_srt(content)
