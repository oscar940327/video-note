from videonote.video_service import audio_is_complete, normalize_video_url


def test_normalize_bilibili_url_removes_tracking_parameters():
    url = "https://www.bilibili.com/video/BV1X6Vo6EEMs/?-Arouter=story&buvid=tracking"
    assert normalize_video_url(url) == "https://www.bilibili.com/video/BV1X6Vo6EEMs/"


def test_normalize_youtube_url_keeps_only_video_id():
    url = "https://www.youtube.com/watch?v=abc123&utm_source=test"
    assert normalize_video_url(url) == "https://www.youtube.com/watch?v=abc123"


def test_unknown_url_is_unchanged():
    url = "https://example.com/video?id=1"
    assert normalize_video_url(url) == url


def test_audio_completeness_uses_decodable_packet_duration(monkeypatch, tmp_path):
    media = tmp_path / "audio.m4a"
    media.write_bytes(b"test")
    monkeypatch.setattr("videonote.video_service.audio_packet_duration", lambda path: 140.0)

    complete, duration = audio_is_complete(media, expected_duration=1600.0)

    assert complete is False
    assert duration == 140.0


def test_audio_completeness_accepts_small_duration_difference(monkeypatch, tmp_path):
    media = tmp_path / "audio.m4a"
    media.write_bytes(b"test")
    monkeypatch.setattr("videonote.video_service.audio_packet_duration", lambda path: 1580.0)

    complete, _ = audio_is_complete(media, expected_duration=1600.0)

    assert complete is True
