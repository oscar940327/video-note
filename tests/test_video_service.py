from videonote.video_service import normalize_video_url


def test_normalize_bilibili_url_removes_tracking_parameters():
    url = "https://www.bilibili.com/video/BV1X6Vo6EEMs/?-Arouter=story&buvid=tracking"
    assert normalize_video_url(url) == "https://www.bilibili.com/video/BV1X6Vo6EEMs/"


def test_normalize_youtube_url_keeps_only_video_id():
    url = "https://www.youtube.com/watch?v=abc123&utm_source=test"
    assert normalize_video_url(url) == "https://www.youtube.com/watch?v=abc123"


def test_unknown_url_is_unchanged():
    url = "https://example.com/video?id=1"
    assert normalize_video_url(url) == url
