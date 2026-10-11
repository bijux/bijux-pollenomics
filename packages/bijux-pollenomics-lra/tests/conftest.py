from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests/reference")]


@pytest.fixture(scope="session")
def project_root() -> Path:
    return ROOT
