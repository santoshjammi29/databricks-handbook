"""
Test Suite: Secret Sanitization & Unregistered UUID Leakage Detection.
"""

import re

from handbook.curriculum import REGISTERED_MOCK_UUIDS

UUID_REGEX = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)


def test_no_unregistered_uuids(base_dir):
    """Ensures no real corporate credentials or unexpected UUIDs leak into content files."""
    scan_paths = [
        *list((base_dir / "notebooks").glob("*/*.py")),
        *list((base_dir / "resources").glob("*.yml")),
        base_dir / "databricks.yml",
    ]

    unregistered_findings = []
    for p in scan_paths:
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for m in UUID_REGEX.finditer(text):
            found_uuid = m.group(0).lower()
            if found_uuid not in REGISTERED_MOCK_UUIDS:
                rel = p.relative_to(base_dir)
                unregistered_findings.append(f"{rel}: {found_uuid}")

    assert not unregistered_findings, (
        f"Found {len(unregistered_findings)} unregistered UUID(s):\n"
        + "\n".join(unregistered_findings)
    )
