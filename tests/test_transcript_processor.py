from videonote.models import TranscriptSegment
from videonote.transcript_processor import chunk_segments, clean_segments


def test_clean_segments_deduplicates_and_merges_short_text():
    source = [
        TranscriptSegment(0, 1, "same sentence"),
        TranscriptSegment(1, 2, "same sentence"),
        TranscriptSegment(2, 3, "short"),
        TranscriptSegment(3, 4, "This is a sufficiently long next segment for the test."),
    ]
    cleaned = clean_segments(source, min_chars=10)
    assert cleaned[0].text == "same sentence short"
    assert cleaned[0].end == 3
    assert len(cleaned) == 2


def test_chunk_segments_keeps_time_ranges():
    source = [
        TranscriptSegment(0, 1, "a" * 8),
        TranscriptSegment(1, 2, "b" * 8),
        TranscriptSegment(2, 3, "c" * 8),
    ]
    chunks = chunk_segments(source, max_chars=18)
    assert len(chunks) == 2
    assert (chunks[0].start, chunks[0].end) == (0, 2)
    assert (chunks[1].start, chunks[1].end) == (2, 3)
