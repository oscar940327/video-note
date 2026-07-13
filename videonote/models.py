from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class VideoInfo:
    url: str
    video_id: str
    title: str
    platform: str
    duration: float | None = None
    thumbnail: str | None = None
    uploader: str | None = None
    webpage_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Transcript:
    video: VideoInfo
    language: str
    source: str
    segments: list[TranscriptSegment] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(segment.text for segment in self.segments if segment.text.strip())

    def to_dict(self) -> dict[str, Any]:
        return {
            "video": self.video.to_dict(),
            "language": self.language,
            "source": self.source,
            "segments": [segment.to_dict() for segment in self.segments],
        }


@dataclass
class TranscriptChunk:
    start: float
    end: float
    text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
