"""
Unit tests for handbook.curriculum registry and module specifications.
"""

from handbook.curriculum import (
    MODULES,
    TOTAL_ARCHITECTURES,
    TOTAL_FLASHCARDS,
    TOTAL_INTERVIEW_GUIDES,
    TOTAL_MODULES,
    TOTAL_NOTEBOOKS,
    TOTAL_RUNBOOKS,
    TOTAL_TOPICS,
    TOTAL_WHITEBOARDS,
)


def test_modules_count_and_continuity():
    assert len(MODULES) == TOTAL_MODULES
    assert len(MODULES) == 10

    # Ensure continuous range from 1 to 105 without gaps or overlaps
    current_expected_id = 1
    for mod in MODULES:
        assert mod.id_start == current_expected_id
        assert mod.id_end >= mod.id_start
        assert mod.expected_count == (mod.id_end - mod.id_start + 1)
        current_expected_id = mod.id_end + 1

    assert current_expected_id - 1 == TOTAL_NOTEBOOKS
    assert TOTAL_NOTEBOOKS == 105


def test_curriculum_constants():
    assert TOTAL_WHITEBOARDS == 52
    assert TOTAL_RUNBOOKS == 6
    assert TOTAL_ARCHITECTURES == 4
    assert TOTAL_INTERVIEW_GUIDES == 5
    assert TOTAL_FLASHCARDS == 50
    assert TOTAL_TOPICS == 132
