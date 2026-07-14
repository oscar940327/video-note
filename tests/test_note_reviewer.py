from videonote.note_reviewer import apply_safe_review_edits, replace_section


def test_safe_review_edits_require_a_unique_exact_anchor():
    markdown = "# Note\n\nA wrong term.\n\nRepeated. Repeated.\n"
    review = {
        "safe_edits": [
            {"find": "wrong term", "replace": "correct term", "reason": "Transcript"},
            {"find": "Repeated", "replace": "Changed", "reason": "Not unique"},
        ],
        "ambiguities": [],
    }

    result, stats = apply_safe_review_edits(markdown, review)

    assert "correct term" in result
    assert "Changed" not in result
    assert stats == {"applied": 1, "skipped": 1}


def test_ambiguity_is_marked_next_to_its_anchor():
    markdown = "# Note\n\nThe log reports 21.\n"
    review = {
        "safe_edits": [],
        "ambiguities": [{
            "anchor": "The log reports 21.",
            "message": "The narration later says 2.",
            "timestamp": "00:15:20",
        }],
    }

    result, stats = apply_safe_review_edits(markdown, review)

    assert "[!warning] 需要人工確認 [00:15:20]" in result
    assert stats["applied"] == 1


def test_replace_section_changes_only_the_requested_section():
    markdown = "# Note\n\n## One\n\nOld.\n\n## Two\n\nKeep.\n"
    result, replaced = replace_section(markdown, "One", "## One\n\nNew.")

    assert replaced is True
    assert "## One\n\nNew." in result
    assert "## Two\n\nKeep." in result
