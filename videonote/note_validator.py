from __future__ import annotations

import re
from typing import Any

import yaml


def format_validation(markdown: str) -> dict[str, Any]:
    """Validate deterministic Markdown structure without calling an LLM."""
    errors: list[str] = []
    warnings: list[str] = []
    h1 = re.findall(r"^#\s+(.+)$", markdown, re.MULTILINE)
    heading_matches = list(re.finditer(r"^(#{1,6})\s+(.+)$", markdown, re.MULTILINE))
    fences = re.findall(r"^```", markdown, re.MULTILINE)
    if len(h1) != 1:
        errors.append(f"Expected exactly one H1 title, found {len(h1)}.")
    if len(fences) % 2:
        errors.append("Code fences are not balanced.")

    levels = [len(match.group(1)) for match in heading_matches]
    for previous, current in zip(levels, levels[1:]):
        if current > previous + 1:
            warnings.append(f"Heading level jumps from H{previous} to H{current}.")

    names = [match.group(2).strip() for match in heading_matches]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        warnings.append(f"Duplicate headings: {', '.join(duplicates)}")

    for index, match in enumerate(heading_matches):
        end = heading_matches[index + 1].start() if index + 1 < len(heading_matches) else len(markdown)
        if len(match.group(1)) > 1 and not markdown[match.end():end].strip():
            warnings.append(f"Empty section: {match.group(2).strip()}")

    frontmatter = re.match(r"^---\s*\n([\s\S]*?)\n---", markdown)
    if not frontmatter:
        errors.append("YAML Frontmatter is missing.")
    else:
        try:
            data = yaml.safe_load(frontmatter.group(1))
            if not isinstance(data, dict):
                errors.append("YAML Frontmatter must be an object.")
            else:
                required = (
                    "title", "source", "platform", "source_language",
                    "note_language", "created", "tags",
                )
                for key in required:
                    if key not in data:
                        warnings.append(f"Frontmatter field is missing: {key}")
        except yaml.YAMLError as error:
            errors.append(f"Invalid YAML Frontmatter: {error}")

    if "```mermaid" in markdown and not re.search(
        r"```mermaid\s*\n(?:flowchart|graph|sequenceDiagram|classDiagram|stateDiagram)", markdown
    ):
        warnings.append("Mermaid block does not start with a recognized diagram type.")
    return {"passed": not errors, "errors": errors, "warnings": warnings}
