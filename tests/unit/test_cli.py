"""
Unit tests for handbook.cli entry point and subcommands.
"""

import pytest

from handbook.cli import main


def test_cli_help(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "The Databricks Handbook Developer" in captured.out


def test_cli_build_check(capsys):
    assert main(["build", "--check"]) == 0
    captured = capsys.readouterr()
    assert "zero drift" in captured.out


def test_cli_validate_fast(capsys):
    assert main(["validate", "--fast"]) == 0
    captured = capsys.readouterr()
    assert "All 105 Databricks notebooks verified successfully" in captured.out


def test_cli_validate_targets(capsys):
    assert main(["validate", "--target", "links"]) == 0
    assert main(["validate", "--target", "bundle"]) == 0
    assert main(["validate", "--target", "hygiene"]) == 0
    assert main(["validate", "--target", "notebooks"]) == 0
    captured = capsys.readouterr()
    assert "relative links" in captured.out
    assert "Databricks Asset Bundle verified" in captured.out
    assert "Repository hygiene" in captured.out
