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
        assert "Remediation" in content or "Recovery" in content, (
            f"{f.name} missing remediation section"
        )


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


def test_interview_guides_have_no_placeholders_or_mislabeled_fences(base_dir):
    import ast
    import json
    import re

    import yaml

    for md_path in sorted((base_dir / "interview").glob("0[1-4]_*.md")):
        content = md_path.read_text(encoding="utf-8")
        assert not re.search(r"^\s*SELECT\s+1;\s*$", content, re.MULTILINE), (
            f"{md_path.name} still contains placeholder `SELECT 1;` code blocks"
        )
        assert "11111111-2222-3333-4444-555555555555" not in content, (
            f"{md_path.name} contains fake UUID literal `11111111-2222-3333-4444-555555555555`"
        )
        for idx, py_block in enumerate(re.findall(r"```python\n(.*?)```", content, re.DOTALL)):
            try:
                ast.parse(py_block)
            except SyntaxError as exc:
                raise AssertionError(
                    f"{md_path.name} has non-Python or invalid syntax in ```python block #{idx}: {exc}"
                ) from exc
        for idx, json_block in enumerate(re.findall(r"```json\n(.*?)```", content, re.DOTALL)):
            try:
                json.loads(json_block)
            except json.JSONDecodeError as exc:
                raise AssertionError(
                    f"{md_path.name} has invalid JSON in ```json block #{idx}: {exc}"
                ) from exc
        for idx, yaml_block in enumerate(
            re.findall(r"```(?:yaml|yml)\n(.*?)```", content, re.DOTALL)
        ):
            try:
                docs = list(yaml.safe_load_all(yaml_block))
            except yaml.YAMLError as exc:
                raise AssertionError(
                    f"{md_path.name} has invalid YAML in ```yaml block #{idx}: {exc}"
                ) from exc
            assert docs and docs != [None], f"{md_path.name} has empty ```yaml block #{idx}"

    q1 = (base_dir / "interview" / "01_junior_and_associate_databricks_engineer.md").read_text(
        encoding="utf-8"
    )
    assert "100 commits" not in q1, "Q1.2 must cite Delta's default 10-commit checkpoint interval"


def test_flashcards_answers_are_substantive_not_prompts(base_dir):
    import re

    fc_text = (base_dir / "interview" / "05_flashcards_deck_50.md").read_text(encoding="utf-8")
    assert "100 commits" not in fc_text, (
        "Flashcard #2 must cite Delta's 10-commit checkpoint interval"
    )
    answers = re.findall(r"\*\*Answer:\*\*\s*(.+)", fc_text)
    assert len(answers) == TOTAL_FLASHCARDS
    for idx, ans in enumerate(answers, start=1):
        stripped = ans.strip()
        assert not re.match(r"^(How|Why|What|When)\b", stripped), (
            f"Flashcard #{idx} answer looks like a prompt summary instead of a direct answer: {stripped}"
        )
        assert len(stripped) >= 60, f"Flashcard #{idx} answer is unexpectedly thin: {stripped}"


def test_manifest_and_roadmap_difficulty_tiers_synced(base_dir):
    import json
    import re

    mastery_to_tier = {
        "Foundational": "L1",
        "Intermediate": "L2",
        "Advanced": "L3",
        "Architect": "L4",
    }
    manifest = json.loads((base_dir / "manifest.json").read_text(encoding="utf-8"))
    entries = manifest["entries"]
    assert len(entries) == manifest["entry_count"]

    expected_by_id: dict[str, str] = {}
    path_by_id: dict[str, str] = {}
    for entry in entries:
        tier = entry["difficulty"]
        target_path = base_dir / entry["relative_path"]
        assert target_path.exists(), (
            f"manifest.json {entry['id']} points to missing path: {entry['relative_path']}"
        )
        if entry["type"] == "notebook_recipe":
            nb_text = target_path.read_text(encoding="utf-8")
            m = re.search(r"\*\*Mastery Level\*\*:\s*`([^`]+)`", nb_text)
            assert m is not None, f"Missing Mastery Level in {entry['relative_path']}"
            expected = mastery_to_tier[m.group(1)]
            assert tier == expected, (
                f"manifest.json {entry['id']} has difficulty={tier}, expected {expected}"
            )
        expected_by_id[entry["id"]] = tier
        path_by_id[entry["id"]] = entry["relative_path"]

    roadmap_text = (base_dir / "docs" / "ROADMAP.md").read_text(encoding="utf-8")
    roadmap_matches = re.findall(
        r"^- \[ \] `([^`]+)` — \[[^\]]+\]\(([^)]+)\) `(L[1-4])`$",
        roadmap_text,
        re.MULTILINE,
    )
    assert len(roadmap_matches) == len(entries), (
        f"Expected {len(entries)} entries in docs/ROADMAP.md, found {len(roadmap_matches)}"
    )
    roadmap_by_id = {entry_id: tier for entry_id, _link, tier in roadmap_matches}
    assert roadmap_by_id == expected_by_id
    for entry_id, link, _tier in roadmap_matches:
        resolved = (base_dir / "docs" / link).resolve()
        assert resolved.exists(), f"docs/ROADMAP.md {entry_id} broken link: {link}"
        assert resolved == (base_dir / path_by_id[entry_id]).resolve(), (
            f"docs/ROADMAP.md {entry_id} links to {link}, expected {path_by_id[entry_id]}"
        )

    # Verify each entry appears inside a matching Level X subsection in ROADMAP.md
    current_tier: str | None = None
    for line in roadmap_text.splitlines():
        m_tier_hdr = re.search(r"Tier [1-4]: .+ \(Level (1|2|3|4)\)", line)
        if m_tier_hdr:
            current_tier = f"L{m_tier_hdr.group(1)}"
        m_item = re.match(r"^- \[ \] `([^`]+)` .* `(L[1-4])`$", line)
        if m_item:
            assert current_tier == m_item.group(2), (
                f"ROADMAP entry {m_item.group(1)} ({m_item.group(2)}) nested under {current_tier}"
            )
