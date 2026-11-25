"""
Test Suite: Secret Sanitization, Token Pattern Scanning & Unregistered UUID Leakage Detection.
"""

import re
from pathlib import Path

from handbook.curriculum import REGISTERED_MOCK_UUIDS

UUID_REGEX = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)

TOKEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("GitHub Classic PAT", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("GitHub Fine-Grained PAT", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("AWS Access Key ID", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack Token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b")),
    ("Stripe Live Key", re.compile(r"\bsk_live_[0-9a-zA-Z]{16,}\b")),
    ("GCP API Key", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b")),
    ("Private Key Header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)

ALLOWLISTED_TEACHING_TOKENS: frozenset[str] = frozenset(
    {
        "sk_live_998877665544332211",  # Deliberate teaching fake in notebook 007 / mod01.py
    }
)


def scan_paths_for_tokens(files: list[Path], base_dir: Path) -> list[str]:
    """Scans provided files for secret-like token patterns outside the teaching allowlist."""
    findings: list[str] = []
    for p in files:
        if not p.exists() or not p.is_file():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in TOKEN_PATTERNS:
            for m in pattern.finditer(text):
                token = m.group(0)
                if token not in ALLOWLISTED_TEACHING_TOKENS:
                    rel = p.relative_to(base_dir)
                    findings.append(f"{rel} [{label}]: {token[:8]}...")
    return findings


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


def test_no_secret_tokens_in_repo_content(base_dir):
    """Scans src/, notebooks/, resources/, and apps/ for common secret token patterns."""
    scan_paths: list[Path] = [
        *sorted((base_dir / "src").rglob("*.py")),
        *sorted((base_dir / "notebooks").glob("*/*.py")),
        *sorted((base_dir / "resources").glob("*.yml")),
        *sorted((base_dir / "apps").rglob("*.py")),
        *sorted((base_dir / "apps").rglob("*.yaml")),
        base_dir / "databricks.yml",
    ]
    findings = scan_paths_for_tokens(scan_paths, base_dir)
    assert not findings, "Detected unallowlisted secret-like tokens:\n" + "\n".join(findings)
