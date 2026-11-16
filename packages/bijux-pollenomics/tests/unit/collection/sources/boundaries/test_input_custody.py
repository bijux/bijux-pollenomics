"""Boundary decode and provenance checks consume the same bounded bytes."""

from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.boundaries import store
from bijux_pollenomics.collection.sources.boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from tests.support.context_data.boundaries import write_synthetic_boundary_manifest


def _fixture(tmp_path: Path) -> tuple[Path, dict[str, dict[str, Any]]]:
    raw = tmp_path / "boundaries" / "raw"
    raw.mkdir(parents=True)
    countries: dict[str, dict[str, Any]] = {}
    for country, code in BOUNDARY_CODES.items():
        payload = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {"ADM0_A3": code},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[18, 57], [19, 57], [19, 58], [18, 58], [18, 57]]
                        ],
                    },
                }
            ],
        }
        (raw / f"{country.casefold()}.geojson").write_text(json.dumps(payload))
        countries[country] = payload
    write_synthetic_boundary_manifest(raw)
    return raw.parent, countries


def _load(root: Path, **kwargs: Any) -> dict[str, dict[str, object]] | None:
    return store.load_country_boundaries(
        output_root=root,
        boundary_codes=BOUNDARY_CODES,
        natural_earth_version=NATURAL_EARTH_VERSION,
        natural_earth_admin0_url=NATURAL_EARTH_ADMIN0_URL,
        natural_earth_terms_url=NATURAL_EARTH_TERMS_URL,
        **kwargs,
    )


def test_default_loader_cannot_decode_another_buffer_than_the_hashed_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, countries = _fixture(tmp_path)
    sweden = root / "raw/sweden.geojson"
    changed = deepcopy(countries["Sweden"])
    changed["features"][0]["geometry"]["coordinates"][0][0] = [40, 70]
    original_read_text = Path.read_text

    def divergent_read(path: Path, *args: Any, **kwargs: Any) -> str:
        if path == sweden:
            return json.dumps(changed)
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", divergent_read)
    assert _load(root) == countries


def test_injected_reader_supplies_one_buffer_per_literal_source_path(
    tmp_path: Path,
) -> None:
    root, countries = _fixture(tmp_path)
    captured = {path: path.read_bytes() for path in (root / "raw").iterdir()}
    calls: list[Path] = []

    def byte_reader(path: Path) -> bytes:
        calls.append(path)
        raw = captured[path]
        if path.name == "sweden.geojson":
            path.write_bytes(b"replacement after capture")
        return raw

    assert _load(root, byte_reader=byte_reader) == countries
    assert set(calls) == set(captured)
    assert len(calls) == len(set(calls)) == 5
    # The caller owns stability across the operation; this loader uses supplied bytes.
    assert (root / "raw/sweden.geojson").read_bytes() != captured[
        root / "raw/sweden.geojson"
    ]


@pytest.mark.parametrize(
    "filename,budget",
    [("source_manifest.json", 64 * 1024), ("sweden.geojson", 4 * 1024 * 1024)],
)
def test_default_reader_refuses_oversized_sources_before_json_decode(
    tmp_path: Path, filename: str, budget: int
) -> None:
    root, _ = _fixture(tmp_path)
    path = root / "raw" / filename
    raw = path.read_bytes()
    path.write_bytes(raw + b" " * (budget + 1 - len(raw)))
    if filename != "source_manifest.json":
        write_synthetic_boundary_manifest(root / "raw")
    with pytest.raises(ValueError, match="bound|budget"):
        _load(root)


@pytest.mark.parametrize("replacement", [None, "{}", bytearray(b"{}")])
def test_injected_reader_must_return_immutable_bytes(
    tmp_path: Path, replacement: object
) -> None:
    root, _ = _fixture(tmp_path)
    with pytest.raises(ValueError, match="bytes"):
        _load(root, byte_reader=lambda _path: replacement)


def test_injected_reader_remains_subject_to_the_manifest_budget(tmp_path: Path) -> None:
    root, _ = _fixture(tmp_path)
    with pytest.raises(ValueError, match="bound|budget"):
        _load(root, byte_reader=lambda _path: b" " * (64 * 1024 + 1))


@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_default_reader_refuses_aliased_source_members(
    tmp_path: Path, kind: str
) -> None:
    root, _ = _fixture(tmp_path)
    path = root / "raw/sweden.geojson"
    alias = tmp_path / "alias.geojson"
    if kind == "symlink":
        path.rename(alias)
        path.symlink_to(alias)
    else:
        os.link(path, alias)
    with pytest.raises(ValueError, match="regular|alias|symlink"):
        _load(root)


def test_default_reader_refuses_fifo_without_blocking(tmp_path: Path) -> None:
    root, _ = _fixture(tmp_path)
    path = root / "raw/sweden.geojson"
    path.unlink()
    os.mkfifo(path)
    script = """
from pathlib import Path
import sys
from bijux_pollenomics.collection.sources.boundaries.collection import load_country_boundaries
try:
    load_country_boundaries(Path(sys.argv[1]))
except ValueError:
    pass
else:
    raise AssertionError('FIFO source was not refused')
"""
    subprocess.run(
        [sys.executable, "-B", "-c", script, str(root)],
        check=True,
        timeout=5,
        capture_output=True,
    )


@pytest.mark.parametrize(
    "filename,old,new",
    [
        (
            "source_manifest.json",
            '"version": "5.1.1"',
            '"version": "5.1.1", "version": "5.1.1"',
        ),
        ("sweden.geojson", '"ADM0_A3": "SWE"', '"ADM0_A3": "SWE", "ADM0_A3": "SWE"'),
        ("sweden.geojson", '"coordinates": [', '"untrusted": NaN, "coordinates": ['),
        ("sweden.geojson", '"coordinates": [', '"untrusted": 1e400, "coordinates": ['),
    ],
)
def test_boundary_json_does_not_silently_replace_duplicate_or_nonfinite_claims(
    tmp_path: Path, filename: str, old: str, new: str
) -> None:
    root, _ = _fixture(tmp_path)
    path = root / "raw" / filename
    raw = path.read_text()
    assert raw.count(old) == 1
    path.write_text(raw.replace(old, new))
    if filename != "source_manifest.json":
        write_synthetic_boundary_manifest(root / "raw")
    with pytest.raises(ValueError, match="duplicate|nonfinite"):
        _load(root)
