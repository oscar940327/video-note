from videonote.note_generator import repair_note


class FakeClient:
    def __init__(self):
        self.request = None

    def structured(self, **kwargs):
        self.request = kwargs
        return {"markdown": "# Repaired\n\nSupported content."}


def test_repair_note_runs_one_bounded_markdown_pass():
    client = FakeClient()

    result = repair_note(client, "# Draft\n", "[00:00] Transcript")

    assert result == "# Repaired\n\nSupported content.\n"
    assert client.request["name"] == "repaired_video_note"
    assert "CURRENT NOTE\n# Draft" in client.request["input_text"]
    assert "TRANSCRIPT\n[00:00] Transcript" in client.request["input_text"]
