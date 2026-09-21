"""Authenticated multi-site draw intake keeps chronology and source axes."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from shutil import copytree
from types import SimpleNamespace

import numpy as np
import pytest

from bijux_pollenomics.analysis.lra import publication_draws
from bijux_pollenomics.analysis.lra.api import LRARefusal
from bijux_pollenomics.analysis.lra.engine.discovery import (
    MULTISITE_DRAW_LOVE_CAPABILITY,
)
from bijux_pollenomics_lra import api as engine_api


def _bundle(root: Path) -> tuple[Path, np.ndarray]:
    inputs = engine_api.MultisiteRevealsInput(
        site_ids=("small", "large"),
        bin_ids=("recent",),
        taxon_ids=("A", "B", "C"),
        counts=np.array([[[100, 200, 300]], [[300, 200, 100]]]),
        availability=np.ones((2, 1), dtype=bool),
        basin_radius_m=np.array([[25.0], [100.0]]),
        basin_type=np.array([["peatland"], ["lake"]]),
        bin_bounds_bp=np.array([[0.0, 100.0]]),
        ppe=np.array([1.0, 2.0, 3.0]),
        ppe_covariance=np.diag([0.01, 0.04, 0.09]),
        fall_speed_m_s=np.array([0.02, 0.03, 0.04]),
    )
    draws = {"recent": np.tile([[0, 0], [0, 1], [1, 0], [1, 1]], (250, 1))}
    result = engine_api.run_reveals_multisite(
        inputs,
        engine_api.PublicationRevealsConfig("synthetic-bp-v1"),
        bootstrap_indices=draws,
    )
    destination = root / "regional"
    result.write(destination)
    return destination, result.regional_cover_draws["recent"]


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _pin(root: Path) -> str:
    return _digest(root / "checksums.json")


def _repin_member(root: Path, name: str) -> str:
    checksums = root / "checksums.json"
    inventory = json.loads(checksums.read_text())
    member = root / name
    inventory[name] = {"sha256": _digest(member), "bytes": member.stat().st_size}
    checksums.write_text(json.dumps(inventory, indent=2) + "\n")
    return _pin(root)


def test_authenticated_draw_source_retains_bp_axes_and_selected_capability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, expected = _bundle(tmp_path)
    requested = []

    def binding(*, required_capability: str) -> SimpleNamespace:
        requested.append(required_capability)
        return SimpleNamespace(api=engine_api)

    monkeypatch.setattr(publication_draws, "load_engine", binding)
    source = publication_draws.read_multisite_regional_draw_source(
        root, bin_id="recent", expected_checksums_sha256=_pin(root)
    )
    assert requested == [MULTISITE_DRAW_LOVE_CAPABILITY]
    assert (source.younger_bp, source.older_bp) == (0.0, 100.0)
    assert source.regional_site_ids == source.eligible_site_ids == ("small", "large")
    assert source.parent_manifest_sha256 == _digest(root / "run-manifest.json")
    assert source.draw_member_sha256 == _digest(
        root / "regional-cover-draws" / "bin-0.csv"
    )
    assert not source.values.flags.writeable
    np.testing.assert_allclose(source.values, expected, rtol=0, atol=2e-16)


def test_draw_intake_requires_external_pin_and_refuses_member_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _bundle(tmp_path)
    pin = _pin(root)
    monkeypatch.setattr(
        publication_draws,
        "load_engine",
        lambda **_: SimpleNamespace(api=engine_api),
    )
    with pytest.raises(LRARefusal, match="pinned digest"):
        publication_draws.read_multisite_regional_draw_source(
            root, bin_id="recent", expected_checksums_sha256="0" * 64
        )
    draw = root / "regional-cover-draws" / "bin-0.csv"
    draw.write_text(draw.read_text().replace("0,", "9,", 1))
    with pytest.raises(LRARefusal, match="Bundle member differs"):
        publication_draws.read_multisite_regional_draw_source(
            root, bin_id="recent", expected_checksums_sha256=pin
        )


def test_legacy_bundle_without_explicit_bp_and_relabelled_availability_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _bundle(tmp_path)
    monkeypatch.setattr(
        publication_draws,
        "load_engine",
        lambda **_: SimpleNamespace(api=engine_api),
    )
    legacy = tmp_path / "legacy"
    copytree(root, legacy)
    manifest = legacy / "run-manifest.json"
    document = json.loads(manifest.read_text())
    document["parameters"].pop("bin_bounds_bp")
    manifest.write_text(json.dumps(document, indent=2) + "\n")
    pin = _repin_member(legacy, "run-manifest.json")
    with pytest.raises(LRARefusal, match="Typed BP bounds"):
        publication_draws.read_multisite_regional_draw_source(
            legacy, bin_id="recent", expected_checksums_sha256=pin
        )
    relabel = tmp_path / "relabel"
    copytree(root, relabel)
    availability = relabel / "availability.csv"
    availability.write_text(availability.read_text().replace("small", "fabricated"))
    pin = _repin_member(relabel, "availability.csv")
    with pytest.raises(LRARefusal, match="Availability axes"):
        publication_draws.read_multisite_regional_draw_source(
            relabel, bin_id="recent", expected_checksums_sha256=pin
        )


def test_resealed_false_bp_and_extra_draw_index_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _bundle(tmp_path)
    monkeypatch.setattr(
        publication_draws,
        "load_engine",
        lambda **_: SimpleNamespace(api=engine_api),
    )
    false_bp = tmp_path / "false-bp"
    copytree(root, false_bp)
    manifest = false_bp / "run-manifest.json"
    document = json.loads(manifest.read_text())
    document["parameters"]["bin_bounds_bp"] = [[10.0, 110.0]]
    manifest.write_text(json.dumps(document, indent=2) + "\n")
    pin = _repin_member(false_bp, "run-manifest.json")
    with pytest.raises(LRARefusal, match="source-bound identity"):
        publication_draws.read_multisite_regional_draw_source(
            false_bp, bin_id="recent", expected_checksums_sha256=pin
        )
    extra = tmp_path / "extra-index"
    copytree(root, extra)
    index = extra / "regional-cover-draws" / "index.json"
    entries = json.loads(index.read_text())
    entries.append({**entries[0], "bin_id": "fabricated"})
    index.write_text(json.dumps(entries, indent=2) + "\n")
    pin = _repin_member(extra, "regional-cover-draws/index.json")
    with pytest.raises(LRARefusal, match="draw index differs"):
        publication_draws.read_multisite_regional_draw_source(
            extra, bin_id="recent", expected_checksums_sha256=pin
        )


def test_unselected_member_mutation_after_first_inventory_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _ = _bundle(tmp_path)
    pin = _pin(root)
    selected_bin = publication_draws._selected_bin

    def mutate_after_inventory(*args: object) -> object:
        unselected = root / "site-0" / "cover.csv"
        unselected.write_text(unselected.read_text() + "changed\n")
        return selected_bin(*args)

    monkeypatch.setattr(publication_draws, "_selected_bin", mutate_after_inventory)
    monkeypatch.setattr(
        publication_draws,
        "load_engine",
        lambda **_: SimpleNamespace(api=engine_api),
    )
    with pytest.raises(LRARefusal, match="Bundle member differs"):
        publication_draws.read_multisite_regional_draw_source(
            root, bin_id="recent", expected_checksums_sha256=pin
        )
