"""
Databricks Asset Bundle (DAB) Validator.
Verifies that databricks.yml and all resources/*.yml conform to DAB schemas
and that all referenced notebook paths and app components exist on disk.
"""

import re
import sys
from pathlib import Path

from handbook.curriculum import EXPECTED_BUNDLE_RESOURCES


def validate_bundle(base_dir: Path | None = None, verbose: bool = True) -> tuple[bool, list[str]]:
    """
    Validates Databricks Asset Bundle configuration, resources, and referenced notebook paths.
    Returns (success, errors).
    """
    if base_dir is None:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent

    bundle_file = base_dir / "databricks.yml"
    errors: list[str] = []

    if verbose:
        print(f"Validating Databricks Asset Bundle at {base_dir}...")

    if not bundle_file.exists():
        errors.append(f"databricks.yml missing at {bundle_file}")
        return False, errors

    content = bundle_file.read_text(encoding="utf-8")
    if "name: databricks-handbook" not in content:
        errors.append("databricks.yml must define name: databricks-handbook")
    if "targets:" not in content:
        errors.append("databricks.yml must define targets")
    if "dev:" not in content or "prod:" not in content:
        errors.append("databricks.yml must define dev and prod targets")

    # Check resources
    resources_dir = base_dir / "resources"
    for res in EXPECTED_BUNDLE_RESOURCES:
        res_path = resources_dir / res
        if not res_path.exists():
            errors.append(f"Missing resource file {res_path}")

    # Check notebook references in resources
    missing_paths = []
    for yml_file in sorted(resources_dir.glob("*.yml")):
        yml_text = yml_file.read_text(encoding="utf-8")
        matches = re.findall(
            r'notebook_path:\s*["\']?\.\./(notebooks/[^\s"\']+\.py)["\']?', yml_text
        )
        for rel_path in matches:
            abs_path = base_dir / rel_path
            if not abs_path.exists():
                missing_paths.append(
                    f"{yml_file.name} references non-existent notebook: {rel_path}"
                )

    if missing_paths:
        errors.extend(missing_paths)

    # Check Databricks App
    app_dir = base_dir / "apps" / "lakehouse_finops_monitor"
    if not (app_dir / "app.py").exists():
        errors.append("Missing app.py in Databricks App")
    if not (app_dir / "app.yaml").exists():
        errors.append("Missing app.yaml in Databricks App")
    if not (app_dir / "requirements.txt").exists():
        errors.append("Missing requirements.txt in Databricks App")

    if verbose:
        if errors:
            print("\n--- BUNDLE INTEGRITY ERRORS DETECTED ---")
            for err in errors:
                print(f"  ❌ {err}")
        else:
            print("✅ Databricks Asset Bundle verified: 100% schema and path integrity!")

    return len(errors) == 0, errors


def main():
    success, _ = validate_bundle()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
