"""
Unit tests for handbook.readme (build & matrix), handbook.notebooks.export_ipynb,
and CLI subcommands (readme, export-ipynb, explore, build).
"""

import json
import shutil
from pathlib import Path

import pytest

from handbook.cli import main as cli_main
from handbook.notebooks.export_ipynb import convert_databricks_py_to_ipynb, export_all
from handbook.readme.build import (
    END_MODULES_MARKER,
    generate_modules_table,
    update_readme_blocks,
)
from handbook.readme.matrix import (
    clean_for_table,
    extract_notebook_meta,
    generate_markdown,
    make_wrappable,
)


def test_generate_modules_table_covers_all_modules():
    table = generate_modules_table()
    for idx in range(1, 11):
        assert f"| **{idx:02d}** |" in table


def test_update_readme_blocks_check_and_rewrite(base_dir: Path, tmp_path: Path):
    shutil.copy2(base_dir / "README.md", tmp_path / "README.md")

    assert update_readme_blocks(base_dir=tmp_path, check=True) is True

    # Introduce drift in generated table
    readme = tmp_path / "README.md"
    content = readme.read_text(encoding="utf-8")
    drifted = content.replace("10 Recipes", "99 Recipes")
    readme.write_text(drifted, encoding="utf-8")

    assert update_readme_blocks(base_dir=tmp_path, check=True) is False
    assert update_readme_blocks(base_dir=tmp_path, check=False) is True
    assert update_readme_blocks(base_dir=tmp_path, check=True) is True

    # Remove end marker
    readme.write_text(content.replace(END_MODULES_MARKER, ""), encoding="utf-8")
    assert update_readme_blocks(base_dir=tmp_path, check=True) is False
    assert update_readme_blocks(base_dir=tmp_path, check=False) is False


def test_update_readme_blocks_missing_file(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        update_readme_blocks(base_dir=tmp_path, check=True)


def test_cli_readme_and_check(base_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    shutil.copy2(base_dir / "README.md", tmp_path / "README.md")
    shutil.copy2(base_dir / "databricks.yml", tmp_path / "databricks.yml")
    shutil.copy2(base_dir / "pyproject.toml", tmp_path / "pyproject.toml")

    monkeypatch.chdir(tmp_path)
    assert cli_main(["readme", "--check"]) == 0
    assert cli_main(["readme"]) == 0

    (tmp_path / "README.md").write_text("no markers here\n", encoding="utf-8")
    assert cli_main(["readme", "--check"]) == 1
    assert cli_main(["readme"]) == 1


def test_matrix_helpers_and_generation(base_dir: Path):
    assert clean_for_table("  a | b \n c  ") == "a &#124; b c"
    assert clean_for_table("") == ""
    assert make_wrappable("001_test_nb.py") == "001_&#8203;test_&#8203;nb&#8203;.py"

    sample_nb = (
        base_dir
        / "notebooks"
        / "01_platform_architecture_and_security"
        / "001_split_plane_cloud_architecture_control_plane_classic_compute_and_serverless_networking.py"
    )
    meta = extract_notebook_meta(sample_nb)
    assert meta["id"] == "001"
    assert meta["level"] == "Foundational"
    assert meta["objective"]

    md = generate_markdown()
    assert "## 🗺️ Curriculum Overview & Track Architecture" in md
    assert "001" in md
    assert "105" in md


def test_export_ipynb_single_and_all(base_dir: Path, tmp_path: Path):
    src_nb = (
        base_dir
        / "notebooks"
        / "01_platform_architecture_and_security"
        / "001_split_plane_cloud_architecture_control_plane_classic_compute_and_serverless_networking.py"
    )
    out_nb = tmp_path / "single.ipynb"
    convert_databricks_py_to_ipynb(src_nb, out_nb)
    assert out_nb.exists()

    parsed = json.loads(out_nb.read_text(encoding="utf-8"))
    assert parsed["nbformat"] == 4
    cell_types = {c["cell_type"] for c in parsed["cells"]}
    assert cell_types == {"markdown", "code"}

    # Test export_all against staged notebooks folder
    shutil.copytree(base_dir / "notebooks", tmp_path / "notebooks")
    export_all(base_dir=tmp_path)
    exported = list((tmp_path / "ipynb_export").glob("*/*.ipynb"))
    assert len(exported) == 105


def test_cli_build_export_and_explore(
    base_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys
):
    shutil.copy2(base_dir / "databricks.yml", tmp_path / "databricks.yml")
    shutil.copy2(base_dir / "pyproject.toml", tmp_path / "pyproject.toml")
    shutil.copytree(base_dir / "notebooks", tmp_path / "notebooks")

    monkeypatch.chdir(tmp_path)
    assert cli_main(["build"]) == 0
    assert cli_main(["build", "--check"]) == 0
    assert cli_main(["export-ipynb"]) == 0
    assert len(list((tmp_path / "ipynb_export").glob("*/*.ipynb"))) == 105

    monkeypatch.chdir(base_dir)
    assert cli_main([]) == 0
    assert cli_main(["explore", "--list"]) == 0
    assert cli_main(["explore", "--runbooks"]) == 0
    assert cli_main(["explore", "--architectures"]) == 0
    assert cli_main(["explore", "--interview"]) == 0
    assert cli_main(["explore", "--ecosystem"]) == 0
    assert cli_main(["explore", "025"]) == 0
    out = capsys.readouterr().out
    assert "Liquid Clustering" in out
