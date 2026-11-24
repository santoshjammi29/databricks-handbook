"""
Pytest configuration for The Databricks Handbook test suite.
"""

import sys
from pathlib import Path
import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
src_dir = BASE_DIR / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

@pytest.fixture(scope="session")
def base_dir():
    return BASE_DIR

@pytest.fixture(scope="session")
def notebooks_dir(base_dir):
    return base_dir / "notebooks"
