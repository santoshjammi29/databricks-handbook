"""
Canary test verifying that Gitleaks actively scans generators and notebooks.
Ensures .gitleaks.toml enables default rules and does not blanket-allowlist content directories.
"""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


def _find_gitleaks() -> str | None:
    return shutil.which("gitleaks")


def _synthetic_github_pat() -> str:
    # Build dynamically at runtime so neither source nor .pyc stores a static token literal.
    parts = ["ghp", "9xK2mP7qR4tV8wZ1cB5nF3jL6hD0sA9eG2yU"]
    return "_".join(parts)


def test_gitleaks_canary_catches_leaks_in_generator_and_notebook(base_dir: Path, tmp_path: Path):
    gitleaks_bin = _find_gitleaks()
    if not gitleaks_bin:
        if os.environ.get("CI"):
            pytest.fail("gitleaks binary is required in CI for secret-scanning canary verification")
        pytest.skip("gitleaks binary not installed locally; required in CI")

    config_path = base_dir / ".gitleaks.toml"
    assert config_path.exists(), ".gitleaks.toml missing"

    # Copy one generator and one notebook into tmp_path under their relative repo paths
    gen_rel = Path("src/handbook/generators/mod01.py")
    nb_rel = Path(
        "notebooks/01_platform_architecture_and_security/"
        "001_split_plane_cloud_architecture_control_plane_classic_compute_and_serverless_networking.py"
    )
    canary = _synthetic_github_pat()

    for rel in (gen_rel, nb_rel):
        target = tmp_path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        original = (base_dir / rel).read_text(encoding="utf-8")
        target.write_text(f'{original}\nCANARY_TOKEN = "{canary}"\n', encoding="utf-8")

        res = subprocess.run(  # noqa: S603
            [
                gitleaks_bin,
                "detect",
                "--no-git",
                "--source",
                str(tmp_path),
                "--config",
                str(config_path),
                "--redact",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert res.returncode != 0, (
            f"Gitleaks failed to detect planted canary token in {rel}!\n"
            f"stdout: {res.stdout}\nstderr: {res.stderr}"
        )
        # Clean sub-tree before testing the next target individually
        shutil.rmtree(tmp_path / rel.parts[0])
