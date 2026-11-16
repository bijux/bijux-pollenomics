"""Authenticated multi-site draw intake keeps chronology and source axes."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from shutil import copytree
from types import SimpleNamespace
from typing import Any

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

    def mutate_after_inventory(
        availability: list[list[str]], manifest: dict[str, object], selected_bin_id: str
    ) -> object:
        unselected = root / "site-0" / "cover.csv"
        unselected.write_text(unselected.read_text() + "changed\n")
        return selected_bin(availability, manifest, selected_bin_id)

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


def test_parser_path_replacement_cannot_return_B_with_A_source_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import csv
    import io

    root, expected = _bundle(tmp_path)
    member = root / "regional-cover-draws/bin-0.csv"
    original = member.read_bytes()
    rows = list(csv.reader(io.StringIO(original.decode())))
    rows[1][1:] = ["1", "0", "0"]
    changed = io.StringIO()
    csv.writer(changed, lineterminator="\n").writerows(rows)
    replacement = changed.getvalue().encode()
    actual_open = io.open
    events: list[str] = []

    class RestoredParser:
        def __init__(self, stream: Any) -> None:
            self.stream = stream

        def __enter__(self):  # type: ignore[no-untyped-def]
            return self.stream.__enter__()

        def __exit__(self, *args):  # type: ignore[no-untyped-def]
            result = self.stream.__exit__(*args)
            member.write_bytes(original)
            events.append("restored_A_after_actual_parser_close")
            return result

    def parser_open(path, *args, **kwargs):  # type: ignore[no-untyped-def]
        mode = kwargs.get("mode", args[0] if args else "r")
        if not isinstance(path, int) and Path(path) == member and mode == "r":
            member.write_bytes(replacement)
            events.append("B_before_actual_parser_open")
            return RestoredParser(actual_open(path, *args, **kwargs))
        return actual_open(path, *args, **kwargs)

    monkeypatch.setattr(io, "open", parser_open)
    try:
        source = publication_draws.read_multisite_regional_draw_source(
            root, bin_id="recent", expected_checksums_sha256=_pin(root)
        )
    except LRARefusal:
        assert events
    else:
        np.testing.assert_allclose(source.values, expected, rtol=0, atol=2e-16)
        assert source.draw_member_sha256 == sha256(original).hexdigest()
    assert member.read_bytes() == original


@pytest.mark.parametrize(
    "member_name",
    [
        "checksums.json",
        "run-manifest.json",
        "availability.csv",
        "regional-cover-draws/index.json",
        "regional-cover-draws/bin-0.csv",
    ],
)
@pytest.mark.parametrize("change", ["growth", "early_eof", "replacement"])
def test_selected_buffer_refuses_actual_descriptor_source_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, member_name: str, change: str
) -> None:
    import os

    from bijux_pollenomics.core.filesystem import BoundedInputTree

    root, _ = _bundle(tmp_path)
    pin = _pin(root)
    member = root / member_name
    size = member.stat().st_size
    original_tree_read, original_read = BoundedInputTree._read, os.read
    events: list[str] = []
    reads: list[int] = []
    descriptors: set[int] = set()

    def selected_read(tree, name, *, retain, max_bytes=None):  # type: ignore[no-untyped-def]
        if tree.root == root and name == member_name and retain:

            def mutate_before_read(descriptor: int, bound: int) -> bytes:
                descriptors.add(descriptor)
                if not events:
                    if change == "replacement":
                        member.rename(member.with_name("retained-original"))
                        member.write_bytes(b"B" * size)
                    else:
                        os.truncate(
                            member,
                            size + 1024 * 1024 if change == "growth" else size - 1,
                        )
                    events.append(change)
                block = original_read(descriptor, bound)
                reads.append(len(block))
                return block

            with monkeypatch.context() as mutation:
                mutation.setattr(os, "read", mutate_before_read)
                return original_tree_read(
                    tree, name, retain=retain, max_bytes=max_bytes
                )
        return original_tree_read(tree, name, retain=retain, max_bytes=max_bytes)

    monkeypatch.setattr(BoundedInputTree, "_read", selected_read)
    with pytest.raises(LRARefusal):
        publication_draws.read_multisite_regional_draw_source(
            root, bin_id="recent", expected_checksums_sha256=pin
        )
    assert events == [change] and sum(reads) <= size + 1
    assert descriptors
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)


def test_draw_array_above_control_receipt_size_remains_source_bounded(
    tmp_path: Path,
) -> None:
    import csv
    from io import StringIO

    root, expected = _bundle(tmp_path)
    member = root / "regional-cover-draws/bin-0.csv"
    rows = list(csv.reader(StringIO(member.read_text())))
    for row in rows[1:]:
        row[1:] = [" " * 400 + value for value in row[1:]]
    content = StringIO()
    csv.writer(content, lineterminator="\n").writerows(rows)
    member.write_text(content.getvalue())
    assert member.stat().st_size > 1024 * 1024
    pin = _repin_member(root, "regional-cover-draws/bin-0.csv")
    source = publication_draws.read_multisite_regional_draw_source(
        root, bin_id="recent", expected_checksums_sha256=pin
    )
    np.testing.assert_allclose(source.values, expected, rtol=0, atol=2e-16)


@pytest.mark.parametrize("size", [True, 1.0, -1, "1"])
def test_source_byte_profile_requires_native_nonnegative_sizes(
    tmp_path: Path,
    size: object,
) -> None:
    root, _ = _bundle(tmp_path)
    path = root / "checksums.json"
    checksums = json.loads(path.read_bytes())
    checksums["availability.csv"]["bytes"] = size
    path.write_text(json.dumps(checksums))
    with pytest.raises(LRARefusal, match="Malformed bundle checksum"):
        publication_draws.read_multisite_regional_draw_source(
            root, bin_id="recent", expected_checksums_sha256=_pin(root)
        )
