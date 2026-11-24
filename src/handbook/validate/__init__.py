"""
Validation Suite for The Databricks Handbook.
"""

from pathlib import Path

from handbook.validate.bundle import validate_bundle
from handbook.validate.hygiene import validate_hygiene
from handbook.validate.links import validate_links
from handbook.validate.notebooks import validate_notebooks


def validate_all(
    base_dir: Path | None = None,
    fast: bool = False,
    verbose: bool = True,
) -> tuple[bool, list[str]]:
    """
    Runs all validators across the repository.
    Returns (success, errors).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

    all_errors: list[str] = []

    # 1. Notebooks validation
    _, nb_errs = validate_notebooks(base_dir, verbose=verbose)
    all_errors.extend(nb_errs)

    # 2. Bundle validation
    _, b_errs = validate_bundle(base_dir, verbose=verbose)
    all_errors.extend(b_errs)

    # 3. Hygiene validation
    _, h_errs = validate_hygiene(base_dir, verbose=verbose)
    all_errors.extend(h_errs)

    # 4. Links validation (skipped if fast=True)
    if not fast:
        _, l_errs = validate_links(base_dir, verbose=verbose)
        all_errors.extend(l_errs)

    return len(all_errors) == 0, all_errors
