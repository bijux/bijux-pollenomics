"""Exercise actual source transport and artifact containment refusals."""

from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "adna_source_view", Path(__file__).with_name("source_view.py")
    )
    assert spec is not None and spec.loader is not None
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def manifest(tmp_path: Path, *, gzip_source: bool = False) -> Path:
    code = module()
    data = tmp_path / "data/source"
    data.parent.mkdir()
    content = b"source-native\n"
    rows = [
        {"path": "data/source", "bytes": len(content), "sha256": code.digest(content)}
    ]
    if gzip_source:
        stored = gzip.compress(content, mtime=0)
        metadata = json.dumps(
            {
                "content_encoding": "gzip",
                "byte_size": len(content),
                "storage_byte_size": len(stored),
            }
        ).encode()
        for suffix, blob in [(".gz", stored), (".metadata.json", metadata)]:
            data.with_name(data.name + suffix).write_bytes(blob)
            rows.append(
                {
                    "path": "data/source" + suffix,
                    "bytes": len(blob),
                    "sha256": code.digest(blob),
                }
            )
    else:
        data.write_bytes(content)
    target = tmp_path / "manifest.json"
    target.write_text(json.dumps({"inputs": rows}))
    return target


@pytest.mark.parametrize("gzip_source", [False, True])
def test_exact_declared_source_view(tmp_path: Path, gzip_source: bool) -> None:
    code = module()
    source = manifest(tmp_path, gzip_source=gzip_source)
    output = tmp_path / "artifacts/source-view"
    code.prepare(tmp_path, output, source)
    assert (output / "data/source").read_bytes() == b"source-native\n"


@pytest.mark.parametrize(
    "relative", ["../escape", "/outside", "packages/undeclared", "data/../outside"]
)
def test_refuse_source_escape(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ValueError):
        module().input_path(tmp_path, relative)


@pytest.mark.parametrize("relative", ["outside", "artifacts/../outside", "artifacts"])
def test_refuse_output_escape(tmp_path: Path, relative: str) -> None:
    source = manifest(tmp_path)
    with pytest.raises(ValueError):
        module().prepare(tmp_path, tmp_path / relative, source)
    assert not (tmp_path / "outside").exists()


def test_changed_source_refused(tmp_path: Path) -> None:
    source = manifest(tmp_path)
    (tmp_path / "data/source").write_bytes(b"changed")
    with pytest.raises(ValueError, match="identity"):
        module().prepare(tmp_path, tmp_path / "artifacts/refused", source)


def test_symlink_source_refused(tmp_path: Path) -> None:
    source = manifest(tmp_path)
    data = tmp_path / "data/source"
    data.unlink()
    data.symlink_to(source)
    with pytest.raises(ValueError, match="Symlink"):
        module().prepare(tmp_path, tmp_path / "artifacts/refused", source)


def test_existing_output_refused(tmp_path: Path) -> None:
    source = manifest(tmp_path)
    output = tmp_path / "artifacts/existing"
    output.mkdir(parents=True)
    with pytest.raises(ValueError, match="new owned"):
        module().prepare(tmp_path, output, source)
