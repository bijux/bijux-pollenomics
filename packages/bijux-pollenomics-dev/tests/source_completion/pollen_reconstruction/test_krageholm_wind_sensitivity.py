"""Source custody is required before a conditional wind comparison."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[5]


def producer() -> ModuleType:
    path = (
        ROOT
        / "reports/science/krageholm-static-geometry-sensitivity/wind_sensitivity.py"
    )
    spec = importlib.util.spec_from_file_location("krageholm_wind_sensitivity", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "corruption",
    ["digest", "size", "missing", "parent", "absolute", "symlink", "root_symlink"],
)
def test_source_mutation_refuses_before_evaluation(
    tmp_path: Path, corruption: str
) -> None:
    module = producer()
    root = tmp_path / "source"
    root.mkdir()
    source = root / "sample.json"
    source.write_bytes(b"retained source")
    custody = {
        "sample.json": {
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "bytes": source.stat().st_size,
        }
    }
    module.verify_sources(root, custody)
    if corruption == "digest":
        source.write_bytes(b"changed source!")
    elif corruption == "size":
        custody["sample.json"]["bytes"] = 1
    elif corruption == "missing":
        source.unlink()
    elif corruption == "parent":
        custody = {"../sample.json": custody["sample.json"]}
    elif corruption == "absolute":
        custody = {str(source): custody["sample.json"]}
    elif corruption == "symlink":
        source.unlink()
        other = tmp_path / "other.json"
        other.write_bytes(b"retained source")
        source.symlink_to(other)
    else:
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        root = alias
    with pytest.raises(ValueError):
        module.verify_sources(root, custody)
