"""
Markdown Relative Link and Anchor Fragment Validator.
Verifies that all internal links and in-page anchor fragments resolve cleanly.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


def github_slug(heading: str) -> str:
    """Converts a markdown heading to GitHub anchor slug."""
    s = heading.strip().lower()
    s = re.sub(r"<\/?[\w\s=\"\'-]+>", "", s)
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    return s


def extract_anchors(content: str) -> Set[str]:
    """Extracts all possible anchor identifiers from a markdown document."""
    anchors: Set[str] = set()

    # Explicit HTML anchor tags: <a id="..."> or <a name="...">
    for m in re.finditer(r'<a\s+[^>]*(?:name|id)=["\']([^"\']+)["\']', content, re.I):
        anchors.add(m.group(1).lower())
        anchors.add(m.group(1))

    # Headings (# Header)
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            h = re.sub(r"^#+\s*", "", line)
            h = re.sub(r"\s*#+$", "", h)
            slug = github_slug(h)
            if slug:
                anchors.add(slug)

    return anchors


def validate_links(
    base_dir: Optional[Path] = None,
    verbose: bool = True,
    include_agents: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Scans markdown files in the repository for broken relative links and anchors.
    Returns (success, errors).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

    # Collect markdown files, excluding git, venvs, and optionally .agents
    md_files: List[Path] = []
    for p in base_dir.rglob("*.md"):
        parts = p.relative_to(base_dir).parts
        if any(part.startswith(".") for part in parts if part != ".github"):
            if not include_agents and ".agents" in parts:
                continue
            if part in (".git", ".venv", ".cache", ".pytest_cache", ".ruff_cache"):
                continue
        md_files.append(p)

    file_anchors: Dict[Path, Set[str]] = {}
    for p in md_files:
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            file_anchors[p.resolve()] = extract_anchors(content)
        except Exception:
            pass

    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
    errors: List[str] = []

    for p in md_files:
        content = p.read_text(encoding="utf-8", errors="ignore")
        rel_doc = p.relative_to(base_dir)

        # Ignore code blocks to avoid false positives in code samples
        in_code_block = False
        lines = content.splitlines()
        for line_num, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue

            for m in link_re.finditer(line):
                url = m.group(2).strip()
                if not url or url.startswith(("http://", "https://", "mailto:", "ftp:", "file://")):
                    continue

                parts = url.split("#", 1)
                target_path_str = parts[0]
                fragment = parts[1] if len(parts) > 1 else None

                if target_path_str:
                    target_path = (p.parent / target_path_str).resolve()
                    if not target_path.exists():
                        errors.append(f"{rel_doc}:{line_num}: Broken file link -> '{url}'")
                        continue

                    if fragment and target_path in file_anchors:
                        anchors = file_anchors[target_path]
                        if fragment not in anchors and fragment.lower() not in anchors:
                            errors.append(
                                f"{rel_doc}:{line_num}: Broken anchor '#{fragment}' in '{target_path_str}'"
                            )
                else:
                    if fragment:
                        own_anchors = file_anchors.get(p.resolve(), set())
                        if fragment not in own_anchors and fragment.lower() not in own_anchors:
                            errors.append(f"{rel_doc}:{line_num}: Broken in-page anchor '#{fragment}'")

    if verbose:
        if errors:
            print(f"\n--- {len(errors)} BROKEN LINKS / ANCHORS DETECTED ---")
            for err in errors[:25]:
                print(f"  ❌ {err}")
            if len(errors) > 25:
                print(f"  ... and {len(errors) - 25} more")
        else:
            print(f"✅ All relative links and anchors in {len(md_files)} markdown documents verified successfully!")

    return len(errors) == 0, errors


def main():
    success, _ = validate_links()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
