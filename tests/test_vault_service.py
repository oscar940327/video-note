from videonote.config import Settings
from videonote.vault_service import classify_note, save_note


class FakeClient:
    def __init__(self, result):
        self.result = result
        self.request = None

    def structured(self, **kwargs):
        self.request = kwargs
        return self.result


def make_settings(tmp_path):
    return Settings(
        tmp_path / "data", "key", "model", "https://example.com/api/v1",
        "http://localhost", "VideoNote Test", 1000,
        vault_path=tmp_path / "content",
    )


def test_classifier_prefers_existing_folder(tmp_path):
    settings = make_settings(tmp_path)
    (settings.vault_path / "AI Agents").mkdir(parents=True)
    client = FakeClient({
        "action": "use_existing", "folder": "ai agents", "confidence": 0.95,
        "reason": "Agent topic",
    })
    result = classify_note(
        "# Plan and Execute\n\nAgent architecture.",
        client,
        settings,
    )
    assert result["folder"] == "AI Agents"
    assert result["filename"] == "Plan and Execute.md"
    assert client.request["model"] == "qwen/qwen3.5-9b"
    assert client.request["reasoning_enabled"] is False


def test_low_confidence_uses_inbox_and_saves_safely(tmp_path):
    settings = make_settings(tmp_path)
    result = save_note(
        "# Mixed Topic\n\nAmbiguous.",
        client=FakeClient({
            "action": "create_new", "folder": "Random", "confidence": 0.4,
            "reason": "Ambiguous",
        }),
        app_settings=settings,
    )
    assert result["relative_path"] == "Inbox/Mixed Topic.md"
    assert (settings.vault_path / result["relative_path"]).exists()


def test_existing_note_is_not_overwritten_with_different_content(tmp_path):
    settings = make_settings(tmp_path)
    first = save_note("# Note\n\nOne", folder="RAG", app_settings=settings)
    second = save_note("# Note\n\nTwo", folder="RAG", app_settings=settings)
    assert first["relative_path"] == "RAG/Note.md"
    assert second["relative_path"] == "RAG/Note-2.md"
