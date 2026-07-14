from __future__ import annotations

import re
from typing import Any

from .llm_service import OpenRouterClient, load_prompt


SAFE_EDIT_SCHEMA = {
    "type": "object",
    "properties": {
        "find": {"type": "string"},
        "replace": {"type": "string"},
        "reason": {"type": "string"},
    },
    "required": ["find", "replace", "reason"],
    "additionalProperties": False,
}

AMBIGUITY_SCHEMA = {
    "type": "object",
    "properties": {
        "anchor": {"type": "string"},
        "message": {"type": "string"},
        "timestamp": {"type": "string"},
    },
    "required": ["anchor", "message", "timestamp"],
    "additionalProperties": False,
}

CRITICAL_SECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "heading": {"type": "string"},
        "reason": {"type": "string"},
        "evidence": {"type": "string"},
    },
    "required": ["heading", "reason", "evidence"],
    "additionalProperties": False,
}

NOTE_REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "safe_edits": {"type": "array", "items": SAFE_EDIT_SCHEMA},
        "ambiguities": {"type": "array", "items": AMBIGUITY_SCHEMA},
        "critical_sections": {"type": "array", "items": CRITICAL_SECTION_SCHEMA},
        "summary": {"type": "string"},
    },
    "required": ["safe_edits", "ambiguities", "critical_sections", "summary"],
    "additionalProperties": False,
}


def review_note(client: OpenRouterClient, markdown: str, transcript_context: str) -> dict[str, Any]:
    return client.structured(
        name="independent_video_note_review",
        schema=NOTE_REVIEW_SCHEMA,
        instructions=load_prompt("review_note_edits.md"),
        input_text=f"NOTE\n{markdown}\n\nTRANSCRIPT\n{transcript_context}",
        max_output_tokens=6000,
        model=client.settings.review_model,
        reasoning_enabled=False,
    )


def apply_safe_review_edits(markdown: str, review: dict[str, Any]) -> tuple[str, dict[str, int]]:
    """Apply only edits whose exact anchor occurs once; never let the reviewer rewrite the document."""
    applied = 0
    skipped = 0
    result = markdown
    for edit in review.get("safe_edits", []):
        find = str(edit.get("find", ""))
        replacement = str(edit.get("replace", ""))
        if not find or find == replacement or result.count(find) != 1:
            skipped += 1
            continue
        result = result.replace(find, replacement, 1)
        applied += 1

    for item in review.get("ambiguities", []):
        anchor = str(item.get("anchor", ""))
        message = str(item.get("message", "")).strip()
        timestamp = str(item.get("timestamp", "")).strip()
        if not anchor or not message or result.count(anchor) != 1:
            skipped += 1
            continue
        suffix = f" [{timestamp}]" if timestamp else ""
        callout = f"\n\n> [!warning] 需要人工確認{suffix}\n> {message}"
        result = result.replace(anchor, anchor + callout, 1)
        applied += 1
    return result, {"applied": applied, "skipped": skipped}


def find_section(markdown: str, heading: str) -> tuple[int, int, str] | None:
    escaped = re.escape(heading.strip().lstrip("#").strip())
    match = re.search(rf"^(##+)\s+{escaped}\s*$", markdown, re.MULTILINE | re.IGNORECASE)
    if not match:
        return None
    level = len(match.group(1))
    following = re.search(rf"^#{{1,{level}}}\s+.+$", markdown[match.end():], re.MULTILINE)
    end = match.end() + following.start() if following else len(markdown)
    return match.start(), end, markdown[match.start():end].strip()


def replace_section(markdown: str, heading: str, replacement: str) -> tuple[str, bool]:
    found = find_section(markdown, heading)
    if not found:
        return markdown, False
    start, end, _ = found
    return markdown[:start] + replacement.strip() + "\n\n" + markdown[end:].lstrip(), True
