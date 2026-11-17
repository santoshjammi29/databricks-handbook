"""
Pytest configuration for The Databricks Handbook test suite.
"""

import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent

@pytest.fixture(scope="session")
def base_dir():
    return BASE_DIR

@pytest.fixture(scope="session")
def notebooks_dir(base_dir):
    return base_dir / "notebooks"
