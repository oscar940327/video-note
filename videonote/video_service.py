from __future__ import annotations

from pathlib import Path
import re
import time
from typing import Callable
from urllib.parse import urlsplit

import av
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from .models import VideoInfo


ProgressCallback = Callable[[str, float | None], None]


class VideoDownloadError(RuntimeError):
    """A user-facing video download error."""


class _CaptureLogger:
    """Prevent expected browser-cookie fallback errors from polluting the server log."""

    def debug(self, message: str) -> None:
        pass

    def warning(self, message: str) -> None:
        pass

    def error(self, message: str) -> None:
        pass


def normalize_video_url(url: str) -> str:
    """Remove tracking parameters while preserving the stable video identifier."""
    value = str(url).strip()
    parsed = urlsplit(value)
    host = parsed.netloc.lower().split(":", 1)[0]
    if host in {"bilibili.com", "www.bilibili.com", "m.bilibili.com"}:
        match = re.search(r"/(video/(?:BV[0-9A-Za-z]+|av\d+))", parsed.path, re.IGNORECASE)
        if match:
            return f"https://www.bilibili.com/{match.group(1)}/"
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        video_id = re.search(r"(?:^|&)v=([^&]+)", parsed.query)
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id.group(1)}"
    return value


def _friendly_download_error(error: Exception, cookies_from_browser: str | None) -> VideoDownloadError:
    message = str(error)
    if "HTTP Error 514" in message or "Frequency Capped" in message:
        cookie_hint = (
            " The selected browser cookies were used; wait 10-30 minutes before trying again."
            if cookies_from_browser else
            " Wait 10-30 minutes, then retry with Chrome or Edge cookies selected in Note settings."
        )
        return VideoDownloadError("Bilibili temporarily rate-limited the audio download (HTTP 514)." + cookie_hint)
    return VideoDownloadError(message)


def _is_locked_browser_cookie_error(error: Exception) -> bool:
    message = str(error).lower()
    return "could not copy" in message and "cookie database" in message


def _platform(extractor: str, url: str) -> str:
    value = f"{extractor} {url}".lower()
    if "bilibili" in value or "b23.tv" in value:
        return "bilibili"
    if "youtube" in value or "youtu.be" in value:
        return "youtube"
    return extractor.lower() or "unknown"


def ydl_options(cookies_from_browser: str | None = None) -> dict:
    options: dict = {
        "noplaylist": True,
        "quiet": True,
        "no_warnings": False,
        "socket_timeout": 15,
        "retries": 20,
        "fragment_retries": 20,
        "file_access_retries": 3,
        "continuedl": True,
        "nopart": False,
    }
    if cookies_from_browser:
        options["cookiesfrombrowser"] = (cookies_from_browser,)
    return options


def audio_packet_duration(media_path: Path) -> float:
    """Return the last decodable audio packet timestamp instead of trusting container metadata."""
    try:
        with av.open(str(media_path)) as container:
            stream = next((item for item in container.streams if item.type == "audio"), None)
            if stream is None:
                raise VideoDownloadError("The downloaded media does not contain an audio stream.")
            last_end = 0.0
            for packet in container.demux(stream):
                if packet.pts is None:
                    continue
                start = float(packet.pts * stream.time_base)
                packet_duration = float((packet.duration or 0) * stream.time_base)
                last_end = max(last_end, start + packet_duration)
    except (OSError, ValueError, av.error.FFmpegError) as error:
        raise VideoDownloadError(f"The downloaded audio cannot be inspected: {error}") from error
    if last_end <= 0:
        raise VideoDownloadError("The downloaded audio contains no decodable audio packets.")
    return last_end


def audio_is_complete(media_path: Path, expected_duration: float | None, minimum_ratio: float = 0.9) -> tuple[bool, float]:
    packet_duration = audio_packet_duration(media_path)
    if not expected_duration or expected_duration <= 0:
        return True, packet_duration
    return packet_duration / expected_duration >= minimum_ratio, packet_duration


def _remove_audio_downloads(destination: Path) -> None:
    for candidate in destination.glob("audio.*"):
        if candidate.is_file():
            candidate.unlink(missing_ok=True)


def get_video_info(url: str, cookies_from_browser: str | None = None) -> tuple[VideoInfo, dict]:
    url = normalize_video_url(url)
    try:
        options = ydl_options(cookies_from_browser)
        if cookies_from_browser:
            options["logger"] = _CaptureLogger()
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=False)
    except DownloadError as error:
        if cookies_from_browser and _is_locked_browser_cookie_error(error):
            with YoutubeDL(ydl_options()) as ydl:
                info = ydl.extract_info(url, download=False)
            info["_videonote_cookie_fallback"] = True
        else:
            raise _friendly_download_error(error, cookies_from_browser) from error
    if info.get("entries"):
        info = next((item for item in info["entries"] if item), info)
    video = VideoInfo(
        url=url,
        video_id=str(info.get("id") or "unknown"),
        title=str(info.get("title") or info.get("id") or "Untitled video"),
        platform=_platform(str(info.get("extractor_key") or info.get("extractor") or ""), url),
        duration=float(info["duration"]) if info.get("duration") is not None else None,
        thumbnail=info.get("thumbnail"),
        uploader=info.get("uploader") or info.get("channel"),
        webpage_url=info.get("webpage_url") or url,
    )
    return video, info


def download_audio(
    url: str,
    destination: Path,
    cookies_from_browser: str | None = None,
    progress: ProgressCallback | None = None,
    expected_duration: float | None = None,
) -> Path:
    url = normalize_video_url(url)
    destination.mkdir(parents=True, exist_ok=True)

    def hook(data: dict) -> None:
        if not progress or data.get("status") != "downloading":
            return
        total = data.get("total_bytes") or data.get("total_bytes_estimate")
        downloaded = data.get("downloaded_bytes") or 0
        progress("Downloading audio", downloaded / total if total else None)

    class ProgressLogger:
        def debug(self, message: str) -> None:
            if progress and ("retrying" in message.lower() or "timed out" in message.lower()):
                progress("Connection timed out; resuming audio download", None)

        def warning(self, message: str) -> None:
            self.debug(message)

        def error(self, message: str) -> None:
            self.debug(message)

    options = ydl_options(cookies_from_browser)
    options.update({
        "format": "bestaudio/best",
        "outtmpl": str(destination / "audio.%(ext)s"),
        "progress_hooks": [hook],
        "logger": ProgressLogger(),
        "quiet": False,
    })
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                prepared = Path(ydl.prepare_filename(info))
        except DownloadError as error:
            last_error = error
            rate_limited = "HTTP Error 514" in str(error) or "Frequency Capped" in str(error)
            if not rate_limited or attempt == 2:
                raise _friendly_download_error(error, cookies_from_browser) from error
            if progress:
                progress("Bilibili rate limit detected; retrying once in 8 seconds", None)
            time.sleep(8)
            continue

        candidates = [prepared] if prepared.exists() else sorted(
            destination.glob("audio.*"), key=lambda item: item.stat().st_mtime, reverse=True
        )
        if not candidates:
            last_error = FileNotFoundError("Audio download completed but the file could not be found.")
        else:
            selected = candidates[0]
            try:
                complete, packet_duration = audio_is_complete(selected, expected_duration)
            except VideoDownloadError as error:
                last_error = error
            else:
                if complete:
                    return selected
                last_error = VideoDownloadError(
                    f"Downloaded audio is incomplete: decodable packets end at {packet_duration:.1f}s "
                    f"but the video duration is {expected_duration:.1f}s."
                )

        if attempt < 2:
            if progress:
                progress("Downloaded audio is incomplete; starting a clean download", None)
            _remove_audio_downloads(destination)
            options["continuedl"] = False
            options["overwrites"] = True

    raise VideoDownloadError(
        f"Audio remained incomplete after clean download retries. {last_error or ''}".strip()
    )
