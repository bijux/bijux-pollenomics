"""Current whole-site and alias restrictions precede every unit entity access."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)

from .native_products import observe_units


@pytest.mark.parametrize("restriction", ["protected", "alias"])
def test_writer_refuses_current_site_or_geographic_alias_duties_before_unit_read(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    restriction: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        write_neotoma_unit_metadata_archive,
    )

    inputs = unit_products(**{restriction: True})
    opened = observe_units(monkeypatch, set())
    with pytest.raises(ValueError, match="role|scope|protected"):
        write_neotoma_unit_metadata_archive(tmp_path / "archive", **inputs["writer"])
    assert opened == []
    assert not (tmp_path / "archive").exists()


@pytest.mark.parametrize("owner_change", ["database", "site", "span"])
def test_current_owner_or_full_unit_span_change_blocks_before_any_source_body(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    owner_change: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        write_neotoma_unit_metadata_archive,
    )

    inputs = unit_products(owner_change=owner_change)
    opened = observe_units(monkeypatch, set())
    with pytest.raises(ValueError, match="owner|scope|unit"):
        write_neotoma_unit_metadata_archive(tmp_path / "archive", **inputs["writer"])
    assert opened == []


@pytest.mark.parametrize("selector", [True, 100.0, None, 999])
def test_unknown_or_coerced_unit_identity_opens_no_unit_body(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    selector: Any,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        read_neotoma_unit_metadata_entity,
        write_neotoma_unit_metadata_archive,
    )

    from .native_products import pin

    inputs = unit_products()
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])
    opened = observe_units(monkeypatch, set())
    with pytest.raises(ValueError):
        read_neotoma_unit_metadata_entity(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            collection_unit_id=selector,
            **inputs["reader"],
        )
    assert opened == []


@pytest.mark.parametrize(
    "anchor",
    [
        "expected_manifest_sha256",
        "expected_context_sha256",
        "expected_native_archive_sha256",
    ],
)
def test_independent_archive_context_and_native_anchors_cannot_be_substituted(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    anchor: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        read_neotoma_unit_metadata_entity,
        write_neotoma_unit_metadata_archive,
    )

    from .native_products import pin

    inputs = unit_products()
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])
    options = {
        **inputs["reader"],
        "expected_manifest_sha256": pin(output / "manifest.json"),
        anchor: "0" * 64,
    }
    opened = observe_units(monkeypatch, set())
    with pytest.raises(ValueError):
        read_neotoma_unit_metadata_entity(output, collection_unit_id=100, **options)
    assert opened == []


@pytest.mark.parametrize(
    "namespace", ["empty_directory", "symlink", "hardlink", "fifo", "unowned_file"]
)
def test_archive_loader_refuses_foreign_namespace_before_unit_buffer(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    namespace: str,
) -> None:
    import os

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        read_neotoma_unit_metadata_inventory,
        write_neotoma_unit_metadata_archive,
    )

    from .native_products import pin

    inputs = unit_products()
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])
    foreign = output / "foreign"
    if namespace == "empty_directory":
        foreign.mkdir()
    elif namespace == "symlink":
        foreign.symlink_to(inputs["original"])
    elif namespace == "hardlink":
        os.link(output / "index.json", foreign)
    elif namespace == "fifo":
        os.mkfifo(foreign)
    else:
        foreign.write_bytes(b"foreign source file")
    opened = observe_units(monkeypatch, set())
    with pytest.raises(ValueError):
        read_neotoma_unit_metadata_inventory(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            **inputs["reader"],
        )
    assert opened == []
    assert foreign.exists() or foreign.is_symlink()


@pytest.mark.parametrize(
    "claim",
    [
        "current_role",
        "native_span",
        "source_status",
        "scope_basis",
        "scientific_admission",
    ],
)
def test_rehashed_index_or_root_claim_cannot_replace_fresh_source_derivation(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    claim: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        read_neotoma_unit_metadata_inventory,
        write_neotoma_unit_metadata_archive,
    )

    from .native_products import rehash_archive

    inputs = unit_products()
    output = tmp_path / "archive"
    write_neotoma_unit_metadata_archive(output, **inputs["writer"])

    def mutate(document: dict[str, Any]) -> None:
        if claim == "scope_basis":
            document["current_scope_basis_sha256"] = "0" * 64
        elif claim == "scientific_admission":
            document["scientific_admission"] = "admitted"
        elif claim == "current_role":
            document["units"][0]["scope"]["current_role"] = "exposed_development"
        elif claim == "native_span":
            document["units"][0]["scope"]["original_native_dataset_ids"] = [201]
        else:
            document["units"][0]["terminal_status"] = "not_attempted_budget"

    digest = rehash_archive(
        output,
        "manifest.json"
        if claim in {"scope_basis", "scientific_admission"}
        else "index.json",
        mutate,
    )
    opened = observe_units(monkeypatch, set())
    with pytest.raises(ValueError):
        read_neotoma_unit_metadata_inventory(
            output, expected_manifest_sha256=digest, **inputs["reader"]
        )
    assert opened == []


@pytest.mark.parametrize("contradiction", ["http_404", "incomplete", "site", "tls"])
def test_rehashed_source_receipt_metadata_contradiction_refuses_before_entity(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    contradiction: str,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        write_neotoma_unit_metadata_archive,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    from .native_products import pin, rewrite_source

    inputs = unit_products()

    def mutate(document: dict[str, Any], _: Any, root: Path) -> None:
        ref = document["units"][0]["attempts"][0]
        path = root / ref["receipt_file"]
        record = json.loads(path.read_bytes())
        field, value = {
            "http_404": ("http_status", 404),
            "incomplete": ("body_complete", False),
            "site": ("expected_site_id", 999),
            "tls": ("tls_mode", "insecure"),
        }[contradiction]
        record[field] = value
        path.write_bytes(encoded_json(record))
        ref["receipt_sha256"] = pin(path)

    rewrite_source(inputs, mutate)
    opened = observe_units(monkeypatch, set())
    with pytest.raises(ValueError):
        write_neotoma_unit_metadata_archive(tmp_path / "archive", **inputs["writer"])
    assert opened == []


def test_rehashed_foreign_unit_key_cannot_open_a_sibling_receipt(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json

    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        write_neotoma_unit_metadata_archive,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive.files import (
        encoded_json,
    )

    from .native_products import pin, rewrite_source

    inputs = unit_products()
    foreign = tmp_path / "foreign-current-attempt-1.receipt.json"

    def mutate(document: dict[str, Any], control: dict[str, Any], root: Path) -> None:
        entry = document["units"][0]
        ref = entry["attempts"][0]
        record = json.loads((root / ref["receipt_file"]).read_bytes())
        target = control["units"][0]
        target["unit_key"] = "../foreign"
        entry["unit_key"] = "../foreign"
        entry["identity"]["unit_key"] = "../foreign"
        record["request_name"] = "../foreign-current-attempt-1"
        foreign.write_bytes(encoded_json(record))
        ref.update(
            request_name=record["request_name"],
            receipt_file="../" + foreign.name,
            receipt_sha256=pin(foreign),
        )

    rewrite_source(inputs, mutate)
    opened = []
    original_open = capture_opening()

    def observe(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.absolute().resolve() == foreign:
            opened.append(path)
        return original_open(path, *args, **kwargs)

    observe_opening(monkeypatch, observe)
    with pytest.raises(ValueError):
        write_neotoma_unit_metadata_archive(tmp_path / "archive", **inputs["writer"])
    assert opened == []


def test_original_capture_anchor_is_required_even_when_lower_replay_accepts_none(
    unit_products: Callable[..., dict[str, Any]], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        write_neotoma_unit_metadata_archive,
    )

    inputs = unit_products()
    options = {**inputs["writer"], "expected_capture_manifest_sha256": None}
    with pytest.raises(ValueError):
        write_neotoma_unit_metadata_archive(tmp_path / "archive", **options)


def test_external_flat_capture_enumeration_stops_at_its_file_budget(
    unit_products: Callable[..., dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.unit_metadata import (
        metadata,
        write_neotoma_unit_metadata_archive,
    )

    inputs = unit_products()
    monkeypatch.setattr(metadata, "MAX_FILES", 2)
    original_iter = Path.iterdir
    visited = []

    def observed(path: Path) -> Any:
        for member in original_iter(path):
            if path == inputs["source"]:
                visited.append(member)
            yield member

    monkeypatch.setattr(Path, "iterdir", observed)
    with pytest.raises(ValueError):
        write_neotoma_unit_metadata_archive(tmp_path / "archive", **inputs["writer"])
    assert len(visited) <= 3
