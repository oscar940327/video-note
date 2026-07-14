from __future__ import annotations

import re
from datetime import date
from typing import Any

import yaml

from .models import VideoInfo


def _frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    match = re.match(r"^---\s*\n([\s\S]*?)\n---\s*\n?", markdown)
    if not match:
        return {}, markdown.lstrip()
    try:
        parsed = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        parsed = {}
    return (parsed if isinstance(parsed, dict) else {}), markdown[match.end():].lstrip()


def normalize_markdown(
    markdown: str,
    video: VideoInfo,
    plan: dict[str, Any],
    source_language: str,
    output_language: str,
) -> str:
    """Apply only deterministic structural fixes without asking an LLM."""
    data, body = _frontmatter(markdown)
    title = str(plan.get("title") or video.title).strip()
    defaults = {
        "title": title,
        "source": video.webpage_url or video.url,
        "platform": video.platform,
        "source_language": source_language,
        "note_language": output_language,
        "created": date.today().isoformat(),
        "tags": plan.get("tags") or [],
    }
    for key, value in defaults.items():
        if key not in data or data[key] in (None, "", []):
            data[key] = value

    h1_matches = list(re.finditer(r"^#\s+.+$", body, re.MULTILINE))
    if not h1_matches:
        body = f"# {title}\n\n{body}"
    elif len(h1_matches) > 1:
        first_end = h1_matches[0].end()
        body = body[:first_end] + re.sub(r"^#\s+", "## ", body[first_end:], flags=re.MULTILINE)

    heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
    matches = list(heading_pattern.finditer(body))
    for index in range(len(matches) - 1, 0, -1):
        current = matches[index]
        previous = matches[index - 1]
        level = len(current.group(1))
        previous_level = len(previous.group(1))
        if level > previous_level + 1:
            replacement = "#" * (previous_level + 1)
            body = body[:current.start()] + replacement + body[current.start() + level:]

    while True:
        empty = re.search(r"\n(##+)\s+[^\n]+\n\s*(?=\n#{1,6}\s+|\Z)", body)
        if not empty:
            break
        body = body[:empty.start()] + "\n" + body[empty.end():]

    if len(re.findall(r"^```", body, re.MULTILINE)) % 2:
        body = body.rstrip() + "\n\n```\n"

    frontmatter = yaml.safe_dump(data, allow_unicode=True, sort_keys=False).strip()
    return f"---\n{frontmatter}\n---\n\n{body.strip()}\n"
