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
    for parent in [cur] + list(cur.parents):
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
        print(f"✅ All {TOTAL_NOTEBOOKS} notebooks are in sync with source generators (zero drift).")
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

        build_readme()
        print("✅ README updated successfully.")
        return 0
    except Exception as e:
        print(f"❌ Failed to build README: {e}")
        return 1


def cmd_export_ipynb(args, base_dir: Path) -> int:
    export_all(base_dir)
    return 0


def cmd_explore(args, base_dir: Path) -> int:
    from handbook.notebooks import explorer

    # Forward any remaining args to explorer
    orig_argv = sys.argv
    try:
        sys.argv = ["handbook explore"] + getattr(args, "explore_args", [])
        if not getattr(args, "explore_args", []):
            explorer.list_all()
        elif args.explore_args[0] == "--list":
            explorer.list_all()
        elif args.explore_args[0] == "--runbooks":
            explorer.list_runbooks()
        elif args.explore_args[0] == "--architectures":
            explorer.list_architectures()
        elif args.explore_args[0] == "--interview":
            explorer.list_interviews()
        elif args.explore_args[0] == "--ecosystem":
            explorer.list_ecosystem()
        else:
            explorer.inspect_recipe(args.explore_args[0])
        return 0
    finally:
        sys.argv = orig_argv


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
    parser_val = subparsers.add_parser("validate", help="Run repository integrity validation suites")
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
    subparsers.add_parser("readme", help="Rebuild / update README markdown blocks")

    # export-ipynb
    subparsers.add_parser("export-ipynb", help="Export all Databricks source notebooks to standard .ipynb")

    # explore
    parser_explore = subparsers.add_parser("explore", help="Explore catalog, runbooks, architectures, and recipes")
    parser_explore.add_argument("explore_args", nargs="*", help="Arguments for catalog explorer")

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

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
