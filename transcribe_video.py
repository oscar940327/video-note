from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Iterable

import ctranslate2
from faster_whisper import WhisperModel
from yt_dlp import YoutubeDL


def safe_name(name: str) -> str:
    """Remove characters that are invalid in Windows filenames."""
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name.strip(" .")[:150] or "transcript"


def format_timestamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3_600_000)
    minutes, milliseconds = divmod(milliseconds, 60_000)
    secs, milliseconds = divmod(milliseconds, 1_000)
    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def download_audio(
    url: str,
    download_dir: Path,
    cookies_from_browser: str | None = None,
) -> tuple[Path, str]:
    download_dir.mkdir(parents=True, exist_ok=True)

    options = {
        "format": "bestaudio/best",
        "outtmpl": str(download_dir / "%(title).150B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "quiet": False,
        "no_warnings": False,
    }

    if cookies_from_browser:
        # Examples: chrome, edge, firefox
        options["cookiesfrombrowser"] = (cookies_from_browser,)

    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        title = info.get("title") or info.get("id") or "video"
        downloaded = Path(ydl.prepare_filename(info))

    if downloaded.exists():
        return downloaded, title

    # Some extractors may change the extension after preparing the filename.
    candidates = sorted(
        download_dir.glob(f"*[{info.get('id', '')}].*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if candidates:
        return candidates[0], title

    raise FileNotFoundError("音訊下載完成，但找不到下載後的檔案。")


def choose_device(force_cpu: bool) -> tuple[str, str]:
    if not force_cpu and ctranslate2.get_cuda_device_count() > 0:
        return "cuda", "float16"
    return "cpu", "int8"


def transcribe(
    media_path: Path,
    model_name: str,
    language: str | None,
    force_cpu: bool,
):
    device, compute_type = choose_device(force_cpu)
    print(f"\n使用裝置：{device}，compute_type={compute_type}")
    print(f"載入模型：{model_name}（第一次執行會下載模型）")

    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
    )

    segments, info = model.transcribe(
        str(media_path),
        language=language,
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=True,
    )

    print(
        f"偵測語言：{info.language} "
        f"(confidence={info.language_probability:.2f})"
    )
    return list(segments), info.language


def write_outputs(
    segments: Iterable,
    output_dir: Path,
    base_name: str,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_name = safe_name(base_name)

    txt_path = output_dir / f"{base_name}.txt"
    srt_path = output_dir / f"{base_name}.srt"

    segments = list(segments)

    with txt_path.open("w", encoding="utf-8") as txt:
        for segment in segments:
            text = segment.text.strip()
            if text:
                txt.write(text + "\n")

    with srt_path.open("w", encoding="utf-8") as srt:
        for index, segment in enumerate(segments, start=1):
            text = segment.text.strip()
            if not text:
                continue
            srt.write(f"{index}\n")
            srt.write(
                f"{format_timestamp(segment.start)} --> "
                f"{format_timestamp(segment.end)}\n"
            )
            srt.write(text + "\n\n")

    return txt_path, srt_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="下載 YouTube/Bilibili 音訊並產生 TXT、SRT 逐字稿。"
    )
    parser.add_argument("url", help="YouTube 或 Bilibili 影片網址")
    parser.add_argument(
        "--model",
        default="small",
        choices=["tiny", "base", "small", "medium", "large-v3", "turbo"],
        help="Whisper 模型，預設 small；medium/large-v3 較準但較慢。",
    )
    parser.add_argument(
        "--language",
        default=None,
        help="指定語言，例如 zh、en；不填則自動偵測。",
    )
    parser.add_argument(
        "--cookies-from-browser",
        choices=["chrome", "edge", "firefox", "brave", "opera", "vivaldi"],
        help="遇到登入、會員或風控限制時，讀取瀏覽器 Cookies。",
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="強制使用 CPU，不使用 NVIDIA GPU。",
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="完成後保留下載的音訊檔。",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="逐字稿輸出資料夾，預設 output。",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).resolve()
    temp_dir = output_dir / "_audio"

    try:
        print("正在下載音訊……")
        media_path, title = download_audio(
            args.url,
            temp_dir,
            args.cookies_from_browser,
        )
        print(f"音訊檔：{media_path.name}")

        segments, detected_language = transcribe(
            media_path=media_path,
            model_name=args.model,
            language=args.language,
            force_cpu=args.cpu,
        )

        txt_path, srt_path = write_outputs(
            segments,
            output_dir,
            f"{title} [{detected_language}]",
        )

        print("\n完成：")
        print(f"TXT：{txt_path}")
        print(f"SRT：{srt_path}")

        if not args.keep_audio:
            media_path.unlink(missing_ok=True)
            try:
                temp_dir.rmdir()
            except OSError:
                pass

        return 0

    except KeyboardInterrupt:
        print("\n已取消。", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"\n執行失敗：{exc}", file=sys.stderr)
        print(
            "提示：若 Bilibili/YouTube 要求登入，可加上 "
            "--cookies-from-browser chrome 或 edge。",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
