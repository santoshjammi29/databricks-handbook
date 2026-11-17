#!/usr/bin/env python3
"""
Interactive CLI Explorer for The Databricks Handbook:
Search, inspect, and explore 105 Databricks production recipes, architectures, and runbooks.

Usage:
    python scripts/interactive_shell.py 025
    python scripts/interactive_shell.py "liquid clustering"
    python scripts/interactive_shell.py --list
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NOTEBOOKS_DIR = BASE_DIR / "notebooks"

def list_all():
    print("\n📚 The Databricks Handbook: 105 Production Recipes\n" + "=" * 80)
    for mod_dir in sorted(list(NOTEBOOKS_DIR.glob("*"))):
        if not mod_dir.is_dir():
            continue
        print(f"\n📂 {mod_dir.name}:")
        for nb in sorted(list(mod_dir.glob("*.py"))):
            print(f"   ⚡ {nb.name}")
    print("\n" + "=" * 80)

def find_notebook(query: str):
    # Try exact number prefix
    if query.isdigit():
        padded = f"{int(query):03d}"
        matches = list(NOTEBOOKS_DIR.glob(f"*/*{padded}*.py"))
        if matches:
            return matches[0]
            
    # Substring search in filenames
    clean_q = query.lower().replace(" ", "_")
    matches = list(NOTEBOOKS_DIR.glob(f"*/*{clean_q}*.py"))
    if matches:
        return matches[0]
        
    # Search content
    for nb in sorted(list(NOTEBOOKS_DIR.glob("*/*.py"))):
        if query.lower() in nb.read_text(encoding="utf-8").lower():
            return nb
            
    return None

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: python scripts/interactive_shell.py <recipe_number_or_keyword>")
        print("       python scripts/interactive_shell.py --list")
        print("Example: python scripts/interactive_shell.py 025")
        print("         python scripts/interactive_shell.py 'liquid clustering'")
        sys.exit(0)

    if sys.argv[1] == "--list":
        list_all()
        sys.exit(0)

    query = sys.argv[1]
    match = find_notebook(query)
    if not match:
        print(f"❌ No recipe matching '{query}' found in {NOTEBOOKS_DIR}")
        sys.exit(1)

    print(f"\n⚡ Databricks Handbook Recipe: {match.name}")
    print(f"📂 Module: {match.parent.name}")
    print("=" * 80)

    content = match.read_text(encoding="utf-8")
    commands = content.split("# COMMAND ----------")
    
    for cmd in commands:
        cmd_s = cmd.strip()
        if not cmd_s:
            continue
        if "# MAGIC %md" in cmd_s:
            md_lines = [l.replace("# MAGIC ", "").replace("# MAGIC", "") for l in cmd_s.splitlines() if not l.startswith("# Databricks")]
            print("\n".join(md_lines))
            print("-" * 80)
        else:
            code_lines = [l for l in cmd_s.splitlines() if not l.startswith("# Databricks")]
            print("\n[Python / PySpark Code]")
            print("\n".join(code_lines))
            print("-" * 80)

if __name__ == "__main__":
    main()
