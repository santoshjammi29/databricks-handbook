"""
Smoke test suite for pure-Spark local execution with Delta Lake.
Marked with @pytest.mark.spark so they run only when Spark extra is installed
or under the nightly-smoke workflow tier.
"""

import ast

import pytest

# Selected representative pure-Spark notebooks across foundational modules
SMOKE_NOTEBOOK_IDS = ["001", "011", "022", "055", "088"]


@pytest.mark.spark
def test_smoke_local_spark_notebooks_syntax(base_dir):
    """Verifies executable cell structure for local Spark smoke tier."""
    nb_dir = base_dir / "notebooks"
    matched_notebooks = []

    for nb_id in SMOKE_NOTEBOOK_IDS:
        matches = list(nb_dir.glob(f"*/*{nb_id}_*.py"))
        assert len(matches) == 1, (
            f"Expected 1 match for smoke notebook {nb_id}, found {len(matches)}"
        )
        matched_notebooks.append(matches[0])

    assert len(matched_notebooks) == len(SMOKE_NOTEBOOK_IDS)

    for nb in matched_notebooks:
        content = nb.read_text(encoding="utf-8")
        commands = content.split("# COMMAND ----------")
        code_cells = [
            c.strip() for c in commands if c.strip() and not c.strip().startswith("# MAGIC")
        ]
        assert len(code_cells) >= 1, f"Smoke notebook {nb.name} has no executable code cells"
        for _idx, code in enumerate(code_cells):
            clean_lines = [
                line
                for line in code.splitlines()
                if not line.strip().startswith("%") and not line.strip().startswith("# MAGIC")
            ]
            clean_code = "\n".join(clean_lines).strip()
            if clean_code:
                # Assert valid AST
                ast.parse(clean_code)
