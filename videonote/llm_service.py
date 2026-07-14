from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

from .config import ROOT_DIR, Settings, settings
from .models import TranscriptChunk
from .utils import timestamp


class LLMConfigurationError(RuntimeError):
    pass


class LLMResponseError(RuntimeError):
    pass


def load_prompt(name: str) -> str:
    return (ROOT_DIR / "prompts" / name).read_text(encoding="utf-8")


def extract_output_text(response: dict[str, Any]) -> str:
    choices = response.get("choices") or []
    if not choices:
        raise LLMResponseError("The OpenRouter response did not contain a completion choice.")
    message = choices[0].get("message") or {}
    if message.get("refusal"):
        raise LLMResponseError(f"The model refused the request: {message['refusal']}")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        text = "".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
        if text.strip():
            return text
    raise LLMResponseError("The OpenRouter response did not contain message content.")


class OpenRouterClient:
    def __init__(self, app_settings: Settings = settings):
        self.settings = app_settings

    def structured(
        self,
        *,
        name: str,
        schema: dict[str, Any],
        instructions: str,
        input_text: str,
        max_output_tokens: int = 12000,
        model: str | None = None,
        reasoning_enabled: bool | None = None,
    ) -> dict[str, Any]:
        if not self.settings.openrouter_api_key:
            raise LLMConfigurationError(
                "OPENROUTER_API_KEY is missing. Copy .env.example to .env and add your OpenRouter API key."
            )
        payload = {
            "model": model or self.settings.openrouter_model,
            "messages": [
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
            "max_tokens": max_output_tokens,
            "stream": False,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": name,
                    "strict": True,
                    "schema": schema,
                }
            },
            "provider": {"require_parameters": True, "allow_fallbacks": True},
        }
        if reasoning_enabled is not None:
            payload["reasoning"] = {"enabled": reasoning_enabled}
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.settings.openrouter_site_url,
            "X-OpenRouter-Title": self.settings.openrouter_app_title,
        }
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with httpx.Client(timeout=httpx.Timeout(180.0, connect=20.0)) as client:
                    response = client.post(
                        f"{self.settings.openrouter_base_url}/chat/completions", headers=headers, json=payload
                    )
                if response.is_error:
                    raise LLMResponseError(
                        f"OpenRouter returned HTTP {response.status_code}: {response.text[:1000]}"
                    )
                return json.loads(extract_output_text(response.json()))
            except (httpx.HTTPError, json.JSONDecodeError, LLMResponseError) as error:
                last_error = error
                if attempt == 2:
                    break
                time.sleep(1.5 * (attempt + 1))
        raise LLMResponseError(f"OpenRouter request failed after 3 attempts: {last_error}")


SUMMARY_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_points": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["summary", "key_points"],
    "additionalProperties": False,
}


def chunks_as_context(
    chunks: list[TranscriptChunk], client: OpenRouterClient, max_chars: int
) -> str:
    full = "\n\n".join(
        f"[{timestamp(chunk.start)}–{timestamp(chunk.end)}]\n{chunk.text}" for chunk in chunks
    )
    if len(full) <= max_chars:
        return full
    summaries: list[str] = []
    for chunk in chunks:
        result = client.structured(
            name="transcript_chunk_summary",
            schema=SUMMARY_SCHEMA,
            instructions=(
                "Summarize this transcript chunk faithfully. Preserve technical terms and do not add facts. "
                "Return only information supported by the chunk."
            ),
            input_text=f"Time range: {timestamp(chunk.start)}–{timestamp(chunk.end)}\n\n{chunk.text}",
            max_output_tokens=1800,
            model=client.settings.context_model,
            reasoning_enabled=False,
        )
        points = "\n".join(f"- {item}" for item in result["key_points"])
        summaries.append(
            f"[{timestamp(chunk.start)}–{timestamp(chunk.end)}]\n{result['summary']}\n{points}"
        )
    return "\n\n".join(summaries)
