from __future__ import annotations

import json
from datetime import date
from typing import Any

from .llm_service import OpenRouterClient, load_prompt
from .models import VideoInfo


MARKDOWN_SCHEMA = {
    "type": "object",
    "properties": {"markdown": {"type": "string"}},
    "required": ["markdown"],
    "additionalProperties": False,
}


def generate_note(
    client: OpenRouterClient,
    video: VideoInfo,
    plan: dict[str, Any],
    transcript_context: str,
    output_language: str,
    note_style: str,
    grounding_mode: str,
) -> str:
    result = client.structured(
        name="generated_video_note",
        schema=MARKDOWN_SCHEMA,
        instructions=load_prompt("generate_note.md"),
        input_text=(
            f"Today's date: {date.today().isoformat()}\nOutput language: {output_language}\n"
            f"Note style: {note_style}\nGrounding mode: {grounding_mode}\n"
            f"Video metadata: {json.dumps(video.to_dict(), ensure_ascii=False)}\n"
            f"Approved note plan: {json.dumps(plan, ensure_ascii=False)}\n\n"
            f"TRANSCRIPT OR GROUNDED CHUNK SUMMARIES\n{transcript_context}"
        ),
        max_output_tokens=20000,
    )
    return result["markdown"].strip() + "\n"


def repair_note(
    client: OpenRouterClient,
    markdown: str,
    transcript_context: str,
) -> str:
    """Run one bounded review pass that fixes safe issues and marks only ambiguity."""
    result = client.structured(
        name="repaired_video_note",
        schema=MARKDOWN_SCHEMA,
        instructions=load_prompt("repair_note.md"),
        input_text=f"CURRENT NOTE\n{markdown}\n\nTRANSCRIPT\n{transcript_context}",
        max_output_tokens=20000,
    )
    return result["markdown"].strip() + "\n"


def regenerate_section(
    client: OpenRouterClient,
    markdown: str,
    section_heading: str,
    transcript_context: str,
    instruction: str,
) -> str:
    result = client.structured(
        name="regenerated_markdown_section",
        schema={
            "type": "object",
            "properties": {"section_markdown": {"type": "string"}},
            "required": ["section_markdown"],
            "additionalProperties": False,
        },
        instructions=(
            "Rewrite only the requested Markdown section. Start with its ## heading. Keep claims grounded in "
            "the transcript and preserve Video content versus AI supplement labels. Return no other sections."
        ),
        input_text=(
            f"Section: {section_heading}\nUser instruction: {instruction}\n\n"
            f"CURRENT NOTE\n{markdown}\n\nTRANSCRIPT\n{transcript_context}"
        ),
        max_output_tokens=5000,
    )
    return result["section_markdown"].strip()
