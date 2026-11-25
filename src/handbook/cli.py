"""
CLI Interface for The Databricks Handbook tooling.
Usage:
    handbook build [--check]
    handbook validate [--fast]
    handbook readme
    handbook export-ipynb
    handbook explore [args...]
"""

import argparse
import sys
from pathlib import Path

from handbook.curriculum import TOTAL_NOTEBOOKS
from handbook.generators import check_drift, generate_all
from handbook.notebooks.export_ipynb import export_all
from handbook.validate import validate_all
from handbook.validate.bundle import validate_bundle
from handbook.validate.hygiene import validate_hygiene
from handbook.validate.links import validate_links
from handbook.validate.notebooks import validate_notebooks


def find_repo_root() -> Path:
    """Finds repo root by searching upward for databricks.yml or pyproject.toml."""
    cur = Path.cwd()
    for parent in [cur, *list(cur.parents)]:
        if (parent / "databricks.yml").exists() and (parent / "pyproject.toml").exists():
            return parent
    return cur


def cmd_build(args, base_dir: Path) -> int:
    if args.check:
        print("Checking notebook generation drift...")
        ok, diffs = check_drift(base_dir)
        if not ok:
            print("❌ Notebook generation drift detected!")
            for d in diffs:
                print(f"  - {d}")
            print("\nRun 'handbook build' to regenerate notebooks from source generators.")
            return 1
        print(
            f"✅ All {TOTAL_NOTEBOOKS} notebooks are in sync with source generators (zero drift)."
        )
        return 0
    else:
        generate_all(base_dir)
        return 0


def cmd_validate(args, base_dir: Path) -> int:
    target = getattr(args, "target", "all")
    if target == "notebooks":
        ok, _ = validate_notebooks(base_dir)
    elif target == "bundle":
        ok, _ = validate_bundle(base_dir)
    elif target == "links":
        ok, _ = validate_links(base_dir)
    elif target == "hygiene":
        ok, _ = validate_hygiene(base_dir)
    else:
        ok, _ = validate_all(base_dir, fast=getattr(args, "fast", False))
    return 0 if ok else 1


def cmd_readme(args, base_dir: Path) -> int:
    try:
        from handbook.readme.build import build_readme

        check_only = getattr(args, "check", False)
        ok = build_readme(base_dir=base_dir, check=check_only)
        if not ok:
            if check_only:
                print(
                    "❌ README drift or missing generated block markers detected! "
                    "Run 'handbook readme' to regenerate."
                )
            else:
                print("❌ Failed to update README: missing BEGIN/END GENERATED:modules markers.")
            return 1
        if check_only:
            print("✅ README generated blocks are in sync (zero drift).")
        else:
            print("✅ README updated successfully.")
        return 0
    except Exception as e:
        print(f"❌ Failed to process README: {e}")
        return 1


def cmd_export_ipynb(args, base_dir: Path) -> int:
    export_all(base_dir)
    return 0


def cmd_explore(args, base_dir: Path) -> int:
    from handbook.notebooks import explorer

    if getattr(args, "runbooks", False):
        explorer.list_runbooks()
    elif getattr(args, "architectures", False):
        explorer.list_architectures()
    elif getattr(args, "interview", False):
        explorer.list_interviews()
    elif getattr(args, "ecosystem", False):
        explorer.list_ecosystem()
    elif getattr(args, "list", False) or not getattr(args, "query", None):
        explorer.list_all()
    else:
        match = explorer.find_file(args.query)
        if not match:
            print(f"❌ No matching content found for: '{args.query}'")
            return 1
        print(f"\n📖 Found: {match.name}\n" + "=" * 80)
        print(match.read_text(encoding="utf-8"))
        print("=" * 80)
    return 0


def cmd_audit_content(args, base_dir: Path) -> int:
    from handbook.audit import audit_content

    check_only = getattr(args, "check", False)
    ok, counts, errors = audit_content(base_dir=base_dir, write=not check_only, check=check_only)
    summary = ", ".join(f"{k}={v}" for k, v in counts.items())
    if not ok:
        print("❌ Content verification audit failed:")
        for err in errors:
            print(f"  - {err}")
        return 1
    if check_only:
        print(f"✅ Content verification report in sync ({summary}).")
    else:
        print(f"✅ Generated docs/verification.md ({summary}).")
    return 0


def cmd_run_local(args, base_dir: Path) -> int:
    from handbook.runner import resolve_notebook_by_id, run_notebook_local, run_tier_local

    tier = getattr(args, "tier", None)
    target = getattr(args, "target", None)
    if tier:
        ok, errors = run_tier_local(base_dir=base_dir, tier=tier, verbose=True)
        if not ok:
            print(f"❌ Local execution failed for {len(errors)} {tier} notebook(s).")
            return 1
        print(f"✅ All {tier} notebooks executed successfully under local Spark + Delta!")
        return 0

    if not target:
        print("❌ Provide a notebook ID (e.g. '022') or '--tier T2'.")
        return 1

    nb_path = resolve_notebook_by_id(base_dir, target)
    if not nb_path:
        print(f"❌ No notebook found matching ID '{target}'.")
        return 1
    ok, err = run_notebook_local(nb_path)
    if not ok:
        print(f"❌ Execution failed: {err}")
        return 1
    print(f"✅ Executed {nb_path.name} cleanly under local Spark + Delta!")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="handbook",
        description="The Databricks Handbook Developer & Platform CLI Tooling",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # build
    parser_build = subparsers.add_parser("build", help="Generate notebooks or verify drift")
    parser_build.add_argument(
        "--check",
        action="store_true",
        help="Check that notebooks on disk match source generators without modifying files",
    )

    # validate
    parser_val = subparsers.add_parser(
        "validate", help="Run repository integrity validation suites"
    )
    parser_val.add_argument(
        "--target",
        choices=["all", "notebooks", "bundle", "links", "hygiene"],
        default="all",
        help="Specific validation target to run",
    )
    parser_val.add_argument(
        "--fast",
        action="store_true",
        help="Run fast pre-commit validation (skips deep link checking)",
    )

    # readme
    parser_readme = subparsers.add_parser("readme", help="Rebuild / update README markdown blocks")
    parser_readme.add_argument(
        "--check",
        action="store_true",
        help="Verify README generated blocks exist and match without modifying README.md",
    )

    # export-ipynb
    subparsers.add_parser(
        "export-ipynb", help="Export all Databricks source notebooks to standard .ipynb"
    )

    # explore
    parser_explore = subparsers.add_parser(
        "explore", help="Explore catalog, runbooks, architectures, and recipes"
    )
    parser_explore.add_argument("query", nargs="?", help="Recipe ID or search keyword")
    parser_explore.add_argument("--list", action="store_true", help="List all 105 recipes")
    parser_explore.add_argument("--runbooks", action="store_true", help="List incident runbooks")
    parser_explore.add_argument(
        "--architectures", action="store_true", help="List architecture guides"
    )
    parser_explore.add_argument("--interview", action="store_true", help="List interview guides")
    parser_explore.add_argument(
        "--ecosystem", action="store_true", help="Show ecosystem cross-navigation"
    )

    # audit-content
    parser_audit = subparsers.add_parser(
        "audit-content", help="Audit notebook verification tiers and build docs/verification.md"
    )
    parser_audit.add_argument(
        "--check",
        action="store_true",
        help="Verify docs/verification.md and tier metadata have zero drift",
    )

    # run-local
    parser_run = subparsers.add_parser(
        "run-local", help="Execute notebooks locally under Delta-enabled Apache Spark"
    )
    parser_run.add_argument("target", nargs="?", help="Notebook ID (e.g. 022)")
    parser_run.add_argument(
        "--tier",
        choices=["T0", "T1", "T2", "T3"],
        help="Execute all notebooks in a verification tier",
    )

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0

    base_dir = find_repo_root()

    if args.command == "build":
        return cmd_build(args, base_dir)
    elif args.command == "validate":
        return cmd_validate(args, base_dir)
    elif args.command == "readme":
        return cmd_readme(args, base_dir)
    elif args.command == "export-ipynb":
        return cmd_export_ipynb(args, base_dir)
    elif args.command == "explore":
        return cmd_explore(args, base_dir)
    elif args.command == "audit-content":
        return cmd_audit_content(args, base_dir)
    elif args.command == "run-local":
        return cmd_run_local(args, base_dir)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
