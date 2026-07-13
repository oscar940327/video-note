from __future__ import annotations

from typing import Any

from .llm_service import OpenRouterClient, load_prompt
from .models import VideoInfo


SECTION_NAMES = [
    "summary", "why", "core_concepts", "architecture", "components", "workflow",
    "example", "minimal_code", "pros_cons", "comparison", "real_world_use",
    "personal_notes", "references",
]

NOTE_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "video_type": {"type": "string"},
        "main_topic": {"type": "string"},
        "source_language": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "sections": {
            "type": "object",
            "properties": {name: {"type": "boolean"} for name in SECTION_NAMES},
            "required": SECTION_NAMES,
            "additionalProperties": False,
        },
    },
    "required": ["title", "video_type", "main_topic", "source_language", "tags", "sections"],
    "additionalProperties": False,
}


def plan_note(
    client: OpenRouterClient,
    video: VideoInfo,
    transcript_context: str,
    output_language: str,
) -> dict[str, Any]:
    return client.structured(
        name="video_note_plan",
        schema=NOTE_PLAN_SCHEMA,
        instructions=load_prompt("analyze_video.md"),
        input_text=(
            f"Output language: {output_language}\n"
            f"Video title: {video.title}\nPlatform: {video.platform}\nSource URL: {video.webpage_url}\n\n"
            f"TRANSCRIPT\n{transcript_context}"
        ),
        max_output_tokens=2500,
    )
