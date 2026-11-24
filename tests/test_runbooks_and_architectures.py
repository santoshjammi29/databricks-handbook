"""
Test Suite: Architectures, Runbooks, and Interview Guides Integrity.
"""

from handbook.curriculum import (
    TOTAL_ARCHITECTURES,
    TOTAL_FLASHCARDS,
    TOTAL_INTERVIEW_GUIDES,
    TOTAL_RUNBOOKS,
    TOTAL_WHITEBOARDS,
)


def test_architectures_exist(base_dir):
    arch_dir = base_dir / "architectures"
    assert arch_dir.exists() and arch_dir.is_dir()
    arch_files = list(arch_dir.glob("*.md"))
    assert len(arch_files) == TOTAL_ARCHITECTURES, (
        f"Expected {TOTAL_ARCHITECTURES} architecture documents, found {len(arch_files)}"
    )
    for f in arch_files:
        content = f.read_text(encoding="utf-8")
        assert len(content) > 1000, f"{f.name} is too short ({len(content)} bytes)"
        assert "```mermaid" in content, f"{f.name} missing Mermaid architectural diagram"


def test_runbooks_exist(base_dir):
    runbook_dir = base_dir / "runbooks"
    assert runbook_dir.exists() and runbook_dir.is_dir()
    runbook_files = list(runbook_dir.glob("*.md"))
    assert len(runbook_files) == TOTAL_RUNBOOKS, (
        f"Expected {TOTAL_RUNBOOKS} incident runbooks, found {len(runbook_files)}"
    )
    for f in runbook_files:
        content = f.read_text(encoding="utf-8")
        assert len(content) > 1000, f"{f.name} is too short ({len(content)} bytes)"
        assert "Emergency Decision Tree" in content, f"{f.name} missing Emergency Decision Tree"
        assert "Remediation" in content or "Recovery" in content, f"{f.name} missing remediation section"


def test_interview_guides_exist(base_dir):
    interview_dir = base_dir / "interview"
    assert interview_dir.exists() and interview_dir.is_dir()
    interview_files = list(interview_dir.glob("*.md"))
    assert len(interview_files) == TOTAL_INTERVIEW_GUIDES, (
        f"Expected {TOTAL_INTERVIEW_GUIDES} interview guides, found {len(interview_files)}"
    )


def test_flashcards_count(base_dir):
    flashcards_file = base_dir / "interview" / "05_flashcards_deck_50.md"
    assert flashcards_file.exists()
    content = flashcards_file.read_text(encoding="utf-8")
    for i in range(1, TOTAL_FLASHCARDS + 1):
        assert f"{i}." in content, f"Missing flashcard question #{i}"


def test_readme_integrity(base_dir):
    readme_file = base_dir / "README.md"
    assert readme_file.exists()
    content = readme_file.read_text(encoding="utf-8")
    assert "# ⚡ The Databricks Handbook" in content
    assert len(content) > 2000, f"README.md unexpectedly small: {len(content)} bytes"


def test_whiteboard_blueprints_integrity(base_dir):
    wb_dir = base_dir / "assets" / "whiteboards"
    assert wb_dir.exists() and wb_dir.is_dir()
    webp_files = list(wb_dir.glob("*.webp"))
    assert len(webp_files) == TOTAL_WHITEBOARDS, (
        f"Expected {TOTAL_WHITEBOARDS} whiteboard blueprints, found {len(webp_files)}"
    )
