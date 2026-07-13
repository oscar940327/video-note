import pytest

from videonote.config import Settings
from videonote.llm_service import LLMConfigurationError, OpenRouterClient, extract_output_text


def test_extract_output_text():
    response = {"choices": [{"message": {"content": "{\"ok\":true}"}}]}
    assert extract_output_text(response) == '{"ok":true}'


def test_missing_api_key_has_actionable_error(tmp_path):
    client = OpenRouterClient(
        Settings(tmp_path, None, "test", "https://example.com/api/v1", "http://localhost", "VideoNote Test", 1000)
    )
    with pytest.raises(LLMConfigurationError, match="OPENROUTER_API_KEY"):
        client.structured(name="test", schema={"type": "object"}, instructions="x", input_text="y")
