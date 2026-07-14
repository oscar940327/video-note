from __future__ import annotations

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
