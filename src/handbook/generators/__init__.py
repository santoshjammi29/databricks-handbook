"""
Master Generator Suite for The Databricks Handbook.
Coordinates the 10 module generators and provides deterministic drift detection.
"""

import filecmp
import tempfile
from pathlib import Path
from typing import List, Tuple

from handbook.curriculum import MODULES, TOTAL_NOTEBOOKS
from handbook.generators import (
    mod01,
    mod02,
    mod03,
    mod04,
    mod05,
    mod06,
    mod07,
    mod08,
    mod09,
    mod10,
)

GENERATOR_MODULES = [
    mod01,
    mod02,
    mod03,
    mod04,
    mod05,
    mod06,
    mod07,
    mod08,
    mod09,
    mod10,
]


def generate_all(base_dir: Path, verbose: bool = True) -> int:
    """Generate all notebooks into base_dir/notebooks. Returns total notebooks generated."""
    if verbose:
        print(f"=== Generating The Databricks Handbook ({TOTAL_NOTEBOOKS} Notebooks) at {base_dir} ===")

    for idx, (mod, spec) in enumerate(zip(GENERATOR_MODULES, MODULES), 1):
        if verbose:
            print(f"\n--- Running Module {idx:02d} Generator ({spec.name}) ---")
        mod.generate(base_dir)

    all_notebooks = list((base_dir / "notebooks").glob("*/*.py"))
    if verbose:
        print("\n========================================================")
        print(f"Successfully generated {len(all_notebooks)} Databricks notebooks across {len(MODULES)} modules!")
        print("========================================================")

    if len(all_notebooks) != TOTAL_NOTEBOOKS:
        raise ValueError(f"Expected {TOTAL_NOTEBOOKS} notebooks, found {len(all_notebooks)}")

    return len(all_notebooks)


def check_drift(base_dir: Path) -> Tuple[bool, List[str]]:
    """
    Regenerates notebooks into a temporary directory and diffs against base_dir/notebooks.
    Returns (in_sync, differences).
    """
    diffs: List[str] = []
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_base = Path(tmp_dir_str)
        generate_all(tmp_base, verbose=False)

        expected_notebooks = sorted(list((tmp_base / "notebooks").glob("*/*.py")))
        actual_notebooks = sorted(list((base_dir / "notebooks").glob("*/*.py")))

        expected_rel = {p.relative_to(tmp_base): p for p in expected_notebooks}
        actual_rel = {p.relative_to(base_dir): p for p in actual_notebooks}

        # Check missing or extra files
        for rel in expected_rel:
            if rel not in actual_rel:
                diffs.append(f"Missing notebook on disk: {rel}")
        for rel in actual_rel:
            if rel not in expected_rel:
                diffs.append(f"Unexpected ungenerated notebook on disk: {rel}")

        # Check content byte-level equality
        for rel, exp_path in expected_rel.items():
            if rel in actual_rel:
                act_path = actual_rel[rel]
                if not filecmp.cmp(exp_path, act_path, shallow=False):
                    diffs.append(f"Notebook content drift in: {rel}")

    return len(diffs) == 0, diffs
