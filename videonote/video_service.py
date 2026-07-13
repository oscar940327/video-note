from __future__ import annotations

from pathlib import Path
import re
import time
from typing import Callable
from urllib.parse import urlsplit

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
    last_error: DownloadError | None = None
    for attempt in range(2):
        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                prepared = Path(ydl.prepare_filename(info))
            break
        except DownloadError as error:
            last_error = error
            rate_limited = "HTTP Error 514" in str(error) or "Frequency Capped" in str(error)
            if not rate_limited or attempt == 1:
                raise _friendly_download_error(error, cookies_from_browser) from error
            if progress:
                progress("Bilibili rate limit detected; retrying once in 8 seconds", None)
            time.sleep(8)
    else:
        raise _friendly_download_error(last_error or RuntimeError("Audio download failed"), cookies_from_browser)
    if prepared.exists():
        return prepared
    candidates = sorted(destination.glob("audio.*"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError("Audio download completed but the file could not be found.")
    return candidates[0]
