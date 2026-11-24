"""
Test Suite: Databricks Asset Bundle (DAB) Integrity & Resource Verification.
"""

import re
from handbook.curriculum import EXPECTED_BUNDLE_RESOURCES


def test_bundle_config_exists(base_dir):
    bundle_file = base_dir / "databricks.yml"
    assert bundle_file.exists(), "databricks.yml is missing at repository root"
    content = bundle_file.read_text(encoding="utf-8")
    assert "name: databricks-handbook" in content
    assert "targets:" in content
    assert "dev:" in content
    assert "staging:" in content
    assert "prod:" in content


def test_bundle_resources_exist(base_dir):
    resources_dir = base_dir / "resources"
    assert resources_dir.exists() and resources_dir.is_dir()

    for res in EXPECTED_BUNDLE_RESOURCES:
        file_path = resources_dir / res
        assert file_path.exists(), f"Expected bundle resource missing: {res}"


def test_notebook_paths_in_resources_exist(base_dir):
    resources_dir = base_dir / "resources"
    for yml_file in resources_dir.glob("*.yml"):
        content = yml_file.read_text(encoding="utf-8")
        matches = re.findall(r'notebook_path:\s*["\']?\.\./(notebooks/[^\s"\']+\.py)["\']?', content)
        for nb_rel_path in matches:
            nb_abs_path = base_dir / nb_rel_path
            assert nb_abs_path.exists(), f"{yml_file.name} references non-existent notebook: {nb_rel_path}"


def test_databricks_app_integrity(base_dir):
    app_dir = base_dir / "apps" / "lakehouse_finops_monitor"
    assert app_dir.exists(), "apps/lakehouse_finops_monitor directory is missing"
    assert (app_dir / "app.py").exists(), "app.py is missing in apps/lakehouse_finops_monitor"
    assert (app_dir / "app.yaml").exists(), "app.yaml manifest is missing in apps/lakehouse_finops_monitor"
    assert (app_dir / "requirements.txt").exists(), "requirements.txt is missing in apps/lakehouse_finops_monitor"


def test_github_actions_ci_workflow_exists(base_dir):
    workflow_file = base_dir / ".github" / "workflows" / "ci.yml"
    assert workflow_file.exists(), ".github/workflows/ci.yml is missing"
