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


def format_validation(markdown: str) -> dict[str, Any]:
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
    for index, (_, name) in enumerate(headings):
        start_match = list(re.finditer(r"^(#{1,6})\s+(.+)$", markdown, re.MULTILINE))[index]
        end = list(re.finditer(r"^(#{1,6})\s+(.+)$", markdown, re.MULTILINE))[index + 1].start() if index + 1 < len(headings) else len(markdown)
        if not markdown[start_match.end():end].strip():
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
