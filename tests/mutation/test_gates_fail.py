"""
Mutation Test Suite: Proves every repository quality gate fails loudly on injected faults.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

from handbook.cli import main as cli_main
from handbook.generators import check_drift
from handbook.validate.bundle import validate_bundle
from handbook.validate.hygiene import validate_hygiene


def _synthetic_github_pat() -> str:
    parts = ["ghp", "9xK2mP7qR4tV8wZ1cB5nF3jL6hD0sA9eG2yU"]
    return "_".join(parts)


def _stage_repo_subset(src_root: Path, dst_root: Path) -> Path:
    """Copies the non-binary subset of the repository to dst_root for isolated fault injection."""
    copy_dirs = (
        "src",
        "notebooks",
        "resources",
        "apps",
        "runbooks",
        "architectures",
        "interview",
        "docs",
    )
    for d in copy_dirs:
        src_d = src_root / d
        if src_d.exists():
            shutil.copytree(
                src_d,
                dst_root / d,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache"),
            )

    for fname in (
        "databricks.yml",
        "pyproject.toml",
        "README.md",
        "CHANGELOG.md",
        "CITATION.cff",
        ".gitleaks.toml",
    ):
        src_f = src_root / fname
        if src_f.exists():
            shutil.copy2(src_f, dst_root / fname)

    # Mirror the 52 .webp filenames without copying binary payloads
    wb_src = src_root / "assets" / "whiteboards"
    wb_dst = dst_root / "assets" / "whiteboards"
    wb_dst.mkdir(parents=True, exist_ok=True)
    for webp in wb_src.glob("*.webp"):
        (wb_dst / webp.name).write_bytes(b"RIFF\x00\x00\x00\x00WEBP")

    return dst_root


def test_mutation_invalid_yaml_fails_bundle_gate(base_dir: Path, tmp_path: Path):
    repo = _stage_repo_subset(base_dir, tmp_path)
    with (repo / "databricks.yml").open("a", encoding="utf-8") as fh:
        fh.write("\nbroken: [unclosed\n")

    ok, errors = validate_bundle(repo, verbose=False)
    assert not ok, "validate_bundle passed despite malformed YAML in databricks.yml!"
    assert errors


def test_mutation_bad_target_mode_enum_fails_bundle_gate(base_dir: Path, tmp_path: Path):
    repo = _stage_repo_subset(base_dir, tmp_path)
    cfg = repo / "databricks.yml"
    text = cfg.read_text(encoding="utf-8")
    assert "mode: development" in text
    cfg.write_text(text.replace("mode: development", "mode: banana", 1), encoding="utf-8")

    ok, errors = validate_bundle(repo, verbose=False)
    assert not ok, "validate_bundle passed despite invalid target mode 'banana'!"
    assert any("banana" in e or "mode" in e.lower() for e in errors)


def test_mutation_missing_notebook_path_fails_bundle_gate(base_dir: Path, tmp_path: Path):
    repo = _stage_repo_subset(base_dir, tmp_path)
    jobs_yml = repo / "resources" / "jobs.yml"
    text = jobs_yml.read_text(encoding="utf-8")
    replaced = text.replace(
        "033_auto_loader_cloudfiles_directory_listing_vs_file_notifications.py",
        "nonexistent_job_notebook.py",
        1,
    )
    assert replaced != text
    jobs_yml.write_text(replaced, encoding="utf-8")

    ok, errors = validate_bundle(repo, verbose=False)
    assert not ok, "validate_bundle passed despite missing notebook_path in jobs.yml!"
    assert any("nonexistent_job_notebook.py" in e for e in errors)


def test_mutation_missing_dlt_notebook_path_fails_bundle_gate(base_dir: Path, tmp_path: Path):
    repo = _stage_repo_subset(base_dir, tmp_path)
    dlt_yml = repo / "resources" / "dlt_pipelines.yml"
    text = dlt_yml.read_text(encoding="utf-8")
    replaced = text.replace(
        "036_delta_live_tables_dlt_foundations_streaming_tables_vs_materialized_views.py",
        "nonexistent_dlt_notebook.py",
        1,
    )
    assert replaced != text
    dlt_yml.write_text(replaced, encoding="utf-8")

    ok, errors = validate_bundle(repo, verbose=False)
    assert not ok, "validate_bundle passed despite missing DLT notebook path in dlt_pipelines.yml!"
    assert any("nonexistent_dlt_notebook.py" in e for e in errors)


def test_mutation_hand_edited_notebook_fails_build_drift(base_dir: Path, tmp_path: Path):
    repo = _stage_repo_subset(base_dir, tmp_path)
    nb = (
        repo
        / "notebooks"
        / "01_platform_architecture_and_security"
        / "001_split_plane_cloud_architecture_control_plane_classic_compute_and_serverless_networking.py"
    )
    with nb.open("a", encoding="utf-8") as fh:
        fh.write("\n# hand edit drift\n")

    in_sync, diffs = check_drift(repo)
    assert not in_sync, "check_drift passed despite hand-edited notebook!"
    assert diffs


def test_mutation_deleted_readme_marker_fails_readme_check(
    base_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repo = _stage_repo_subset(base_dir, tmp_path)
    readme = repo / "README.md"
    lines = [
        line
        for line in readme.read_text(encoding="utf-8").splitlines(keepends=True)
        if "BEGIN GENERATED:modules" not in line
    ]
    readme.write_text("".join(lines), encoding="utf-8")

    monkeypatch.chdir(repo)
    rc = cli_main(["readme", "--check"])
    assert rc != 0, "handbook readme --check passed despite deleted BEGIN GENERATED:modules marker!"


def test_mutation_readme_count_mismatch_fails_hygiene(base_dir: Path, tmp_path: Path):
    repo = _stage_repo_subset(base_dir, tmp_path)
    readme = repo / "README.md"
    text = readme.read_text(encoding="utf-8")
    assert "105 Recipes" in text
    readme.write_text(text.replace("105 Recipes", "99 Recipes"), encoding="utf-8")

    ok, errors = validate_hygiene(repo, verbose=False)
    assert not ok, (
        "validate_hygiene passed despite README recipe count contradicting curriculum.py!"
    )
    assert errors


def test_mutation_planted_token_fails_gitleaks(base_dir: Path, tmp_path: Path):
    gitleaks_bin = shutil.which("gitleaks")
    if not gitleaks_bin:
        if os.environ.get("CI"):
            pytest.fail("gitleaks binary is required in CI")
        pytest.skip("gitleaks binary not installed locally")

    repo = _stage_repo_subset(base_dir, tmp_path)
    target = repo / "src" / "handbook" / "cli.py"
    token = _synthetic_github_pat()
    with target.open("a", encoding="utf-8") as fh:
        fh.write(f'\nTOKEN = "{token}"\n')

    res = subprocess.run(  # noqa: S603
        [
            gitleaks_bin,
            "detect",
            "--no-git",
            "--source",
            str(repo),
            "--config",
            str(repo / ".gitleaks.toml"),
            "--redact",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode != 0, "gitleaks passed despite planted token in src/handbook/cli.py!"


def test_mutation_missing_runbook_section_fails_hygiene(base_dir: Path, tmp_path: Path):
    repo = _stage_repo_subset(base_dir, tmp_path)
    rb = repo / "runbooks" / "01_driver_and_executor_oom_triage.md"
    text = rb.read_text(encoding="utf-8")
    assert "Emergency Decision Tree" in text
    rb.write_text(text.replace("Emergency Decision Tree", "Notes"), encoding="utf-8")

    ok, errors = validate_hygiene(repo, verbose=False)
    assert not ok, "validate_hygiene passed despite missing Emergency Decision Tree in runbook!"
    assert any("Emergency Decision Tree" in e for e in errors)


def test_mutation_version_mismatch_fails_hygiene(base_dir: Path, tmp_path: Path):
    repo = _stage_repo_subset(base_dir, tmp_path)
    cit = repo / "CITATION.cff"
    text = cit.read_text(encoding="utf-8")
    cit.write_text(text.replace("version: 1.1.0", "version: 9.9.9", 1), encoding="utf-8")

    ok, errors = validate_hygiene(repo, verbose=False)
    assert not ok, "validate_hygiene passed despite CITATION.cff version mismatch!"
    assert any("Version mismatch" in e for e in errors)


def test_mutation_whiteboard_domain_omission_fails_hygiene(base_dir: Path, tmp_path: Path):
    repo = _stage_repo_subset(base_dir, tmp_path)
    readme = repo / "README.md"
    text = readme.read_text(encoding="utf-8")
    readme.write_text(
        text.replace("07_data_modeling_architecture.md", "removed.md"), encoding="utf-8"
    )

    ok, errors = validate_hygiene(repo, verbose=False)
    assert not ok, "validate_hygiene passed despite missing whiteboard domain link in README!"
    assert any("07_data_modeling_architecture.md" in e or "sum to" in e for e in errors)


def test_mutation_verification_doc_drift_fails_audit_check(
    base_dir: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    repo = _stage_repo_subset(base_dir, tmp_path)
    ver_doc = repo / "docs" / "verification.md"
    ver_doc.write_text("# stale\n", encoding="utf-8")

    monkeypatch.chdir(repo)
    assert cli_main(["audit-content", "--check"]) == 1
