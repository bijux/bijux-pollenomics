"""Independent epochs and changed current owner/alias roles precede entity access."""

from dataclasses import replace
import os
from pathlib import Path
from typing import Any

import pytest

from .native_products import make_binding, observe_context_bodies, pin, rehash_archive


@pytest.mark.parametrize(
    "anchor", ["expected_context_sha256", "expected_native_archive_sha256"]
)
def test_forged_current_anchor_refuses_before_context_body(
    site_context_products: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    anchor: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource_entity,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    inputs["reader"]["current"] = replace(inputs["current"], **{anchor: "f" * 64})
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError):
        read_neotoma_context_resource_entity(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            site_id=12,
            resource_kind="lake_candidates",
            **inputs["reader"],
        )
    assert opened == []


@pytest.mark.parametrize("change", ["protected", "alias", "database", "span"])
def test_fresh_current_restriction_or_owner_change_blocks_before_source_body(
    site_context_products: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource_entity,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    current = make_binding(tmp_path / "fresh", change)
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError, match="scope"):
        read_neotoma_context_resource_entity(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            site_id=12,
            resource_kind="lake_candidates",
            original=inputs["original"],
            current=current,
        )
    assert opened == []


@pytest.mark.parametrize("change", ["protected", "alias", "database", "span"])
def test_publication_refuses_fresh_restrictions_before_copying_any_context_body(
    site_context_products: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products(change=change)
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError, match="scope"):
        write_neotoma_context_resource_archive(tmp_path / "archive", **inputs["writer"])
    assert opened == [] and not (tmp_path / "archive").exists()


@pytest.mark.parametrize("field", ["max_requests", "max_total_bytes"])
def test_recorded_source_budget_contradiction_refuses_metadata_before_body(
    site_context_products: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource_inventory,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])

    def mutate(document: Any, control: Any) -> None:
        control["limits"][field] = 1

    digest = rehash_archive(output, mutate)
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError, match="budget"):
        read_neotoma_context_resource_inventory(
            output, expected_manifest_sha256=digest, **inputs["reader"]
        )
    assert opened == []


@pytest.mark.parametrize("kind", ["directory", "fifo", "hardlink", "symlink"])
def test_closed_namespace_refuses_before_context_body(
    site_context_products: Any,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource_inventory,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    path = output / "foreign"
    if kind == "directory":
        path.mkdir()
    elif kind == "fifo":
        os.mkfifo(path)
    elif kind == "hardlink":
        os.link(output / "index.json", path)
    else:
        path.symlink_to(output / "index.json")
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError):
        read_neotoma_context_resource_inventory(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            **inputs["reader"],
        )
    assert opened == [] and path.exists()


def test_source_parent_redirected_after_metadata_guard_refuses_before_body(
    site_context_products: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context_resources import (
        read_neotoma_context_resource_entity,
        reading,
        write_neotoma_context_resource_archive,
    )

    inputs = site_context_products()
    output = tmp_path / "archive"
    write_neotoma_context_resource_archive(output, **inputs["writer"])
    original = reading.response_bound

    def redirected(*args: Any, **kwargs: Any) -> int:
        bound = original(*args, **kwargs)
        (output / "capture").rename(output / "retained-source")
        (output / "capture").symlink_to(
            output / "retained-source", target_is_directory=True
        )
        return bound

    monkeypatch.setattr(reading, "response_bound", redirected)
    opened = observe_context_bodies(monkeypatch, set())
    with pytest.raises(ValueError):
        read_neotoma_context_resource_entity(
            output,
            expected_manifest_sha256=pin(output / "manifest.json"),
            site_id=12,
            resource_kind="lake_candidates",
            **inputs["reader"],
        )
    assert (
        opened == []
        and (output / "capture").is_symlink()
        and (output / "retained-source").is_dir()
    )
