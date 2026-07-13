from __future__ import annotations

import re

from .models import TranscriptChunk, TranscriptSegment


def normalize_text(text: str) -> str:
    text = text.replace("\u200b", " ")
    return re.sub(r"\s+", " ", text).strip()


def clean_segments(segments: list[TranscriptSegment], min_chars: int = 28) -> list[TranscriptSegment]:
    cleaned: list[TranscriptSegment] = []
    for segment in segments:
        text = normalize_text(segment.text)
        if not text:
            continue
        if cleaned and text == cleaned[-1].text:
            cleaned[-1].end = max(cleaned[-1].end, segment.end)
            continue
        if cleaned and len(text) < min_chars:
            cleaned[-1].text = normalize_text(f"{cleaned[-1].text} {text}")
            cleaned[-1].end = max(cleaned[-1].end, segment.end)
        else:
            cleaned.append(TranscriptSegment(segment.start, segment.end, text))
    return cleaned


def chunk_segments(segments: list[TranscriptSegment], max_chars: int = 12000) -> list[TranscriptChunk]:
    chunks: list[TranscriptChunk] = []
    current: list[TranscriptSegment] = []
    size = 0
    for segment in segments:
        extra = len(segment.text) + 1
        if current and size + extra > max_chars:
            chunks.append(TranscriptChunk(current[0].start, current[-1].end, "\n".join(item.text for item in current)))
            current, size = [], 0
        current.append(segment)
        size += extra
    if current:
        chunks.append(TranscriptChunk(current[0].start, current[-1].end, "\n".join(item.text for item in current)))
    return chunks
