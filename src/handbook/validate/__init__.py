"""
Validation Suite for The Databricks Handbook.
"""

from pathlib import Path
from typing import List, Optional, Tuple

from handbook.validate.bundle import validate_bundle
from handbook.validate.hygiene import validate_hygiene
from handbook.validate.links import validate_links
from handbook.validate.notebooks import validate_notebooks


def validate_all(
    base_dir: Optional[Path] = None,
    fast: bool = False,
    verbose: bool = True,
) -> Tuple[bool, List[str]]:
    """
    Runs all validators across the repository.
    Returns (success, errors).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

    all_errors: List[str] = []

    # 1. Notebooks validation
    nb_ok, nb_errs = validate_notebooks(base_dir, verbose=verbose)
    all_errors.extend(nb_errs)

    # 2. Bundle validation
    b_ok, b_errs = validate_bundle(base_dir, verbose=verbose)
    all_errors.extend(b_errs)

    # 3. Hygiene validation
    h_ok, h_errs = validate_hygiene(base_dir, verbose=verbose)
    all_errors.extend(h_errs)

    # 4. Links validation (skipped if fast=True)
    if not fast:
        l_ok, l_errs = validate_links(base_dir, verbose=verbose)
        all_errors.extend(l_errs)

    return len(all_errors) == 0, all_errors
