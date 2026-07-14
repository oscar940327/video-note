from videonote.models import VideoInfo
from videonote.note_generator import generate_note_with_plan


class FakeClient:
    def __init__(self):
        self.request = None

    def structured(self, **kwargs):
        self.request = kwargs
        return {
            "plan": {"title": "Planned", "sections": {}},
            "markdown": "# Planned\n\nSupported content.",
        }


def test_generation_combines_plan_and_complete_note():
    client = FakeClient()
    client.settings = type("Settings", (), {"openrouter_model": "generation-model"})()
    video = VideoInfo("url", "id", "Video", "youtube")

    plan, markdown = generate_note_with_plan(
        client, video, "[00:00] Transcript", "zh-TW", "standard", "assisted"
    )

    assert plan["title"] == "Planned"
    assert markdown == "# Planned\n\nSupported content.\n"
    assert client.request["name"] == "planned_generated_video_note"
    assert client.request["max_output_tokens"] == 20000
    assert client.request["model"] == "generation-model"
