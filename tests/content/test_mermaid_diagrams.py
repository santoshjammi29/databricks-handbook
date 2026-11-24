"""
Test Suite: Mermaid Diagram Parser Invariant Verification.
Enforces AGENTS.md Mermaid parsing rules across all repository markdown documents.
"""

from handbook.validate.hygiene import validate_mermaid_blocks


def test_mermaid_parser_rules(base_dir):
    """Verifies that every Mermaid block parses cleanly without label or note syntax conflicts."""
    all_errors = []
    ignored = {".git", ".venv", ".cache", ".pytest_cache", ".ruff_cache", ".agents"}

    for md_file in base_dir.rglob("*.md"):
        parts = md_file.relative_to(base_dir).parts
        if any(p in ignored for p in parts):
            continue
        content = md_file.read_text(encoding="utf-8", errors="ignore")
        if "```mermaid" in content:
            errors = validate_mermaid_blocks(content, str(md_file.relative_to(base_dir)))
            all_errors.extend(errors)

    assert not all_errors, f"Detected {len(all_errors)} Mermaid syntax issue(s):\n" + "\n".join(
        all_errors
    )
