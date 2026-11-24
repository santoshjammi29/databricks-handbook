"""
Repository Hygiene and Architectural Invariant Validator.
Enforces counts, structure invariants, and Mermaid parsing rules across the repository.
"""

import re
import sys
from pathlib import Path

from handbook.curriculum import (
    EXPECTED_MODULE_FOLDERS,
    TOTAL_ARCHITECTURES,
    TOTAL_FLASHCARDS,
    TOTAL_INTERVIEW_GUIDES,
    TOTAL_NOTEBOOKS,
    TOTAL_RUNBOOKS,
    TOTAL_WHITEBOARDS,
)


def validate_mermaid_blocks(content: str, filename: str) -> list[str]:
    """Validates Mermaid syntax against parser rules in AGENTS.md."""
    errors = []
    mermaid_blocks = re.findall(r"```mermaid\n(.*?)\n```", content, re.DOTALL)

    for block_idx, block in enumerate(mermaid_blocks, 1):
        is_sequence = "sequenceDiagram" in block

        for line_no, line in enumerate(block.splitlines(), 1):
            line_str = line.strip()

            # Rule: No unquoted parentheses in link labels -->|Label (text)|
            # Allowed: -->|"Label (text)"| or -->|Label: text|
            unquoted_paren_match = re.search(
                r"-->\|([^\"\|\n]*\([^\)\|\n]*\)[^\"\|\n]*)\|", line_str
            )
            if unquoted_paren_match:
                lbl = unquoted_paren_match.group(0)
                errors.append(
                    f"{filename} [mermaid {block_idx}:{line_no}]: "
                    f"Unquoted parens in link label: '{lbl}'. Wrap like -->|\"Label\"|"
                )

            # Rule: No raw comparison operators <, >, <= in link labels
            raw_comp_match = re.search(r"-->\|([^\"\|\n]*[<>][^\"\|\n]*)\|", line_str)
            if raw_comp_match:
                comp = raw_comp_match.group(0)
                errors.append(
                    f"{filename} [mermaid {block_idx}:{line_no}]: "
                    f"Raw comparison operator in link label: '{comp}'. Use words or &lt;/&gt;"
                )

            # Rule: No semicolons in sequenceDiagram Notes
            if is_sequence and line_str.startswith("Note") and ";" in line_str:
                errors.append(
                    f"{filename} [mermaid {block_idx}:{line_no}]: "
                    f"Semicolon in sequenceDiagram Note: '{line_str}'. Use comma or colon."
                )

    return errors


def validate_hygiene(base_dir: Path | None = None, verbose: bool = True) -> tuple[bool, list[str]]:
    """
    Validates repository structure invariants, content counts, and diagram integrity.
    Returns (success, errors).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

    errors: list[str] = []

    # 1. Whiteboards count (52 .webp invariant)
    wb_dir = base_dir / "assets" / "whiteboards"
    if wb_dir.exists():
        webp_files = list(wb_dir.glob("*.webp"))
        if len(webp_files) != TOTAL_WHITEBOARDS:
            errors.append(
                f"Expected {TOTAL_WHITEBOARDS} whiteboard .webp files, found {len(webp_files)}"
            )

    # 2. Module directories and total notebooks
    nb_dir = base_dir / "notebooks"
    if nb_dir.exists():
        for mod_folder in EXPECTED_MODULE_FOLDERS:
            folder_path = nb_dir / mod_folder
            if not folder_path.is_dir():
                errors.append(f"Missing expected module directory: {mod_folder}")
        actual_notebooks = list(nb_dir.glob("*/*.py"))
        if len(actual_notebooks) != TOTAL_NOTEBOOKS:
            errors.append(f"Expected {TOTAL_NOTEBOOKS} notebooks, found {len(actual_notebooks)}")

    # 3. Architectures count
    arch_dir = base_dir / "architectures"
    if arch_dir.exists():
        arch_files = list(arch_dir.glob("*.md"))
        if len(arch_files) != TOTAL_ARCHITECTURES:
            errors.append(
                f"Expected {TOTAL_ARCHITECTURES} architecture docs, found {len(arch_files)}"
            )
        for af in arch_files:
            text = af.read_text(encoding="utf-8")
            errors.extend(validate_mermaid_blocks(text, af.name))

    # 4. Runbooks count and invariants
    runbook_dir = base_dir / "runbooks"
    if runbook_dir.exists():
        runbook_files = list(runbook_dir.glob("*.md"))
        if len(runbook_files) != TOTAL_RUNBOOKS:
            errors.append(f"Expected {TOTAL_RUNBOOKS} runbooks, found {len(runbook_files)}")
        for rf in runbook_files:
            text = rf.read_text(encoding="utf-8")
            if "Emergency Decision Tree" not in text:
                errors.append(f"{rf.name}: Missing 'Emergency Decision Tree' section")
            if "Remediation" not in text and "Recovery" not in text:
                errors.append(f"{rf.name}: Missing remediation/recovery section")
            errors.extend(validate_mermaid_blocks(text, rf.name))

    # 5. Interview guides count
    interview_dir = base_dir / "interview"
    if interview_dir.exists():
        int_files = list(interview_dir.glob("*.md"))
        if len(int_files) != TOTAL_INTERVIEW_GUIDES:
            errors.append(
                f"Expected {TOTAL_INTERVIEW_GUIDES} interview guides, found {len(int_files)}"
            )
        flashcards_file = interview_dir / "05_flashcards_deck_50.md"
        if flashcards_file.exists():
            fc_text = flashcards_file.read_text(encoding="utf-8")
            for q_idx in range(1, TOTAL_FLASHCARDS + 1):
                if f"{q_idx}." not in fc_text:
                    errors.append(f"Missing flashcard #{q_idx} in {flashcards_file.name}")

    if verbose:
        if errors:
            print("\n--- HYGIENE ERRORS DETECTED ---")
            for err in errors:
                print(f"  ❌ {err}")
        else:
            print("✅ Repository hygiene and architectural invariants verified successfully!")

    return len(errors) == 0, errors


def main():
    success, _ = validate_hygiene()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
