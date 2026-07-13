import json

from videonote.subtitle_service import choose_subtitle, parse_json_subtitle, parse_vtt_or_srt


def test_manual_subtitle_is_preferred():
    info = {
        "subtitles": {"en": [{"url": "manual"}]},
        "automatic_captions": {"zh": [{"url": "auto"}]},
    }
    assert choose_subtitle(info) == ("manual_subtitle", "en")


def test_chinese_priority_within_manual_subtitles():
    info = {"subtitles": {"en": [{}], "zh-TW": [{}]}}
    assert choose_subtitle(info) == ("manual_subtitle", "zh-TW")


def test_parse_vtt():
    content = """WEBVTT

00:00:01.000 --> 00:00:03.500
Hello <b>world</b>

00:03.500 --> 00:05.000
第二段
"""
    segments = parse_vtt_or_srt(content)
    assert [(item.start, item.end, item.text) for item in segments] == [
        (1.0, 3.5, "Hello world"),
        (3.5, 5.0, "第二段"),
    ]


def test_parse_youtube_json3():
    content = json.dumps({"events": [{"tStartMs": 1000, "dDurationMs": 800, "segs": [{"utf8": "Hi"}]}]})
    segment = parse_json_subtitle(content)[0]
    assert (segment.start, segment.end, segment.text) == (1.0, 1.8, "Hi")
