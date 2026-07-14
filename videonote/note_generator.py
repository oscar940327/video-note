from __future__ import annotations

import json
from datetime import date
from typing import Any

from .llm_service import OpenRouterClient, load_prompt
from .models import VideoInfo
from .note_planner import NOTE_PLAN_SCHEMA


MARKDOWN_SCHEMA = {
    "type": "object",
    "properties": {"markdown": {"type": "string"}},
    "required": ["markdown"],
    "additionalProperties": False,
}

GENERATED_NOTE_SCHEMA = {
    "type": "object",
    "properties": {
        "plan": NOTE_PLAN_SCHEMA,
        "markdown": {"type": "string"},
    },
    "required": ["plan", "markdown"],
    "additionalProperties": False,
}


def generate_note_with_plan(
    client: OpenRouterClient,
    video: VideoInfo,
    transcript_context: str,
    output_language: str,
    note_style: str,
    grounding_mode: str,
) -> tuple[dict[str, Any], str]:
    """Plan and write the complete note in one high-quality model call."""
    result = client.structured(
        name="planned_generated_video_note",
        schema=GENERATED_NOTE_SCHEMA,
        instructions=load_prompt("generate_note_with_plan.md"),
        input_text=(
            f"Today's date: {date.today().isoformat()}\nOutput language: {output_language}\n"
            f"Note style: {note_style}\nGrounding mode: {grounding_mode}\n"
            f"Video metadata: {json.dumps(video.to_dict(), ensure_ascii=False)}\n\n"
            f"TRANSCRIPT OR LOSS-RESISTANT TRANSCRIPT CONTEXT\n{transcript_context}"
        ),
        max_output_tokens=20000,
        model=client.settings.openrouter_model,
    )
    return result["plan"], result["markdown"].strip() + "\n"


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
        model=client.settings.openrouter_model,
    )
    return result["section_markdown"].strip()


def rewrite_critical_section(
    client: OpenRouterClient,
    section_markdown: str,
    issue: dict[str, Any],
    transcript_context: str,
) -> str:
    """Use the generation model only for a reviewer-confirmed major section problem."""
    result = client.structured(
        name="rewritten_critical_section",
        schema={
            "type": "object",
            "properties": {"section_markdown": {"type": "string"}},
            "required": ["section_markdown"],
            "additionalProperties": False,
        },
        instructions=(
            "Repair only the supplied Markdown section for the confirmed major issue. Preserve its heading, useful "
            "supported content, detail level, timestamps, callouts, and writing style. Add or correct only what the "
            "transcript supports. Do not return any other section or commentary."
        ),
        input_text=(
            f"REVIEW FINDING\n{json.dumps(issue, ensure_ascii=False)}\n\n"
            f"SECTION TO REPAIR\n{section_markdown}\n\n"
            f"TRANSCRIPT CONTEXT\n{transcript_context}"
        ),
        max_output_tokens=8000,
        model=client.settings.openrouter_model,
    )
    return result["section_markdown"].strip()
