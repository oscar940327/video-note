from __future__ import annotations

import re
from typing import Any

import yaml

from .llm_service import OpenRouterClient, load_prompt


GROUNDING_SCHEMA = {
    "type": "object",
    "properties": {
        "supported_claims": {"type": "array", "items": {"type": "string"}},
        "unsupported_claims": {"type": "array", "items": {"type": "string"}},
        "missing_key_points": {"type": "array", "items": {"type": "string"}},
        "possible_transcription_errors": {"type": "array", "items": {"type": "string"}},
        "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
    },
    "required": [
        "supported_claims", "unsupported_claims", "missing_key_points",
        "possible_transcription_errors", "overall_score",
    ],
    "additionalProperties": False,
}

REVIEW_START = "<!-- VIDEONOTE_REVIEW_START -->"
REVIEW_END = "<!-- VIDEONOTE_REVIEW_END -->"


def strip_review_annotations(markdown: str) -> str:
    pattern = rf"\n*{re.escape(REVIEW_START)}[\s\S]*?{re.escape(REVIEW_END)}\n*"
    return re.sub(pattern, "\n\n", markdown).strip() + "\n"


def _review_text(item: Any) -> str:
    if isinstance(item, dict):
        parts = [str(value).strip() for value in item.values() if str(value).strip()]
        return " — ".join(parts)
    return str(item).strip().replace("\n", " ")


def annotate_review_items(markdown: str, validation: dict[str, Any]) -> str:
    """Insert one visible, replaceable review callout near the top of a note."""
    clean = strip_review_annotations(markdown)
    items: list[tuple[str, str]] = []
    for error in validation.get("errors", []):
        items.append(("Markdown 錯誤", _review_text(error)))
    for warning in validation.get("warnings", []):
        items.append(("Markdown 警告", _review_text(warning)))

    grounding = validation.get("grounding") or {}
    categories = (
        ("缺少逐字稿支持", "unsupported_claims"),
        ("疑似轉錄錯誤", "possible_transcription_errors"),
        ("可能遺漏的重點", "missing_key_points"),
    )
    for label, key in categories:
        for item in grounding.get(key, []) or []:
            text = _review_text(item)
            if text:
                items.append((label, text))

    if not items:
        return clean

    lines = [
        REVIEW_START,
        "> [!warning] 需要人工檢查",
        "> 以下位置由系統標記，確認後可勾選；重新執行檢查會更新此區塊。",
        ">",
    ]
    lines.extend(f"> - [ ] **{label}**：{text}" for label, text in items)
    lines.append(REVIEW_END)
    block = "\n".join(lines)

    frontmatter = re.match(r"^---\s*\n[\s\S]*?\n---\s*\n?", clean)
    if frontmatter:
        return clean[: frontmatter.end()].rstrip() + "\n\n" + block + "\n\n" + clean[frontmatter.end():].lstrip()
    return block + "\n\n" + clean


def format_validation(markdown: str) -> dict[str, Any]:
    markdown = strip_review_annotations(markdown)
    errors: list[str] = []
    warnings: list[str] = []
    h1 = re.findall(r"^#\s+(.+)$", markdown, re.MULTILINE)
    headings = re.findall(r"^(#{1,6})\s+(.+)$", markdown, re.MULTILINE)
    fences = re.findall(r"^```", markdown, re.MULTILINE)
    if len(h1) != 1:
        errors.append(f"Expected exactly one H1 title, found {len(h1)}.")
    if len(fences) % 2:
        errors.append("Code fences are not balanced.")
    levels = [len(marks) for marks, _ in headings]
    for previous, current in zip(levels, levels[1:]):
        if current > previous + 1:
            warnings.append(f"Heading level jumps from H{previous} to H{current}.")
    names = [name.strip() for _, name in headings]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        warnings.append(f"Duplicate headings: {', '.join(duplicates)}")
    for index, (marks, name) in enumerate(headings):
        start_match = list(re.finditer(r"^(#{1,6})\s+(.+)$", markdown, re.MULTILINE))[index]
        end = list(re.finditer(r"^(#{1,6})\s+(.+)$", markdown, re.MULTILINE))[index + 1].start() if index + 1 < len(headings) else len(markdown)
        # A document title commonly leads directly into its first H2 section.
        # It is structural metadata, not an empty content section.
        if len(marks) > 1 and not markdown[start_match.end():end].strip():
            warnings.append(f"Empty section: {name.strip()}")
    frontmatter = re.match(r"^---\s*\n([\s\S]*?)\n---", markdown)
    if not frontmatter:
        errors.append("YAML Frontmatter is missing.")
    else:
        try:
            data = yaml.safe_load(frontmatter.group(1))
            if not isinstance(data, dict):
                errors.append("YAML Frontmatter must be an object.")
            else:
                for key in ("title", "source", "platform", "source_language", "note_language", "created", "tags"):
                    if key not in data:
                        warnings.append(f"Frontmatter field is missing: {key}")
        except yaml.YAMLError as error:
            errors.append(f"Invalid YAML Frontmatter: {error}")
    if "```mermaid" in markdown and not re.search(r"```mermaid\s*\n(?:flowchart|graph|sequenceDiagram|classDiagram|stateDiagram)", markdown):
        warnings.append("Mermaid block does not start with a recognized diagram type.")
    return {"passed": not errors, "errors": errors, "warnings": warnings}


def validate_grounding(
    client: OpenRouterClient, markdown: str, transcript_context: str
) -> dict[str, Any]:
    return client.structured(
        name="video_note_grounding_validation",
        schema=GROUNDING_SCHEMA,
        instructions=load_prompt("validate_note.md"),
        input_text=f"NOTE\n{markdown}\n\nTRANSCRIPT\n{transcript_context}",
        max_output_tokens=6000,
    )
