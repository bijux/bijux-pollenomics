"""A source archive owns a closed regular namespace and cannot redirect writes."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.resource_catalogue import (
    archive as api,
)
from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
    inventory,
    publication,
)
from bijux_pollenomics.core.filesystem import OwnedTreeWriter
from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)


def baseline(
    make: Callable[..., dict[str, Any]], publish: Callable[..., Any], root: Path
) -> tuple[Path, str, dict[str, Path], Path, str]:
    catalogue, digest, sources = publish(make())
    output = root / "source-resources"
    api.write_neotoma_source_archive(
        output,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=digest,
        capture_sources=sources,
    )
    return (
        catalogue,
        digest,
        sources,
        output,
        sha256((output / "manifest.json").read_bytes()).hexdigest(),
    )


@pytest.mark.parametrize("limit", ["declared_size", "remaining_budget"])
def test_oversized_member_is_refused_before_opening_its_buffer(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    limit: str,
) -> None:
    _, _, _, output, _ = baseline(catalogue_sources, publish_catalogue, tmp_path)
    path = output / "manifest.json"
    manifest = json.loads(path.read_bytes())
    relative = next(iter(manifest["files"]))
    member = output / relative
    size = member.stat().st_size
    assert size > 0
    if limit == "declared_size":
        manifest["files"][relative]["bytes"] = size - 1
        manifest["source_bytes"] -= 1
        path.write_text(json.dumps(manifest))
    raw = path.read_bytes()
    if limit == "remaining_budget":
        monkeypatch.setattr(inventory, "MAX_BYTES", len(raw) + size - 1)
    read = capture_opening()

    def observed(selected: Path, *args: Any, **kwargs: Any) -> Any:
        if selected == member:
            pytest.fail("oversized source member buffer was opened")
        return read(selected, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    message = (
        "bounded regular file"
        if limit == "declared_size"
        else "finite publication budget"
    )
    with pytest.raises(ValueError, match=message):
        api.load_neotoma_source_archive(
            output, expected_manifest_sha256=sha256(raw).hexdigest()
        )


@pytest.mark.parametrize("entry", ["fifo", "empty_directory"])
def test_extra_nonregular_or_unowned_directory_is_not_a_closed_archive(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    entry: str,
) -> None:
    _, _, _, output, digest = baseline(catalogue_sources, publish_catalogue, tmp_path)
    if entry == "fifo":
        os.mkfifo(output / "unowned.pipe")
    else:
        (output / "unowned-empty").mkdir()
    with pytest.raises(ValueError, match="namespace|population|regular|directory"):
        api.load_neotoma_source_archive(output, expected_manifest_sha256=digest)


@pytest.mark.parametrize(
    "claim",
    ["source_scope", "independent_vegetation_accuracy", "unknown_optional_field"],
)
def test_rehashed_manifest_cannot_add_unowned_root_claims(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    claim: str,
) -> None:
    _, _, _, output, _ = baseline(catalogue_sources, publish_catalogue, tmp_path)
    path = output / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest[claim] = True
    path.write_text(json.dumps(manifest))
    digest = sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="manifest|schema|identity|fields"):
        api.load_neotoma_source_archive(output, expected_manifest_sha256=digest)


@pytest.mark.parametrize(
    "redirect", ["staging_symlink", "child_symlink", "child_directory"]
)
def test_filesystem_redirection_never_writes_into_another_directory(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    redirect: str,
) -> None:
    catalogue, digest, sources = publish_catalogue(catalogue_sources())
    final = tmp_path / "source-resources"
    stage = tmp_path / ".source-resources.staging"
    foreign = tmp_path / "another-writer"
    foreign.mkdir()
    (foreign / "user.txt").write_bytes(b"preserve")
    module: Any = publication
    read = module._read
    changed = False

    def swapping(path: Path, bound: int) -> bytes:
        nonlocal changed
        body = read(path, bound)
        assert isinstance(body, bytes)
        if stage.is_dir() and not changed:
            child = stage / "catalogue"
            if redirect == "staging_symlink":
                stage.rename(tmp_path / "owned-stage")
                stage.symlink_to(foreign, target_is_directory=True)
                changed = True
            elif child.is_dir():
                child.rename(tmp_path / "owned-child")
                if redirect == "child_symlink":
                    child.symlink_to(foreign, target_is_directory=True)
                else:
                    foreign.rename(child)
                changed = True
        return body

    # Keep the source reader real; only interpose the filesystem mutation seam.
    monkeypatch.setattr(module, "_read", swapping)
    with pytest.raises((ValueError, OSError)):
        api.write_neotoma_source_archive(
            final,
            catalogue_directory=catalogue,
            expected_catalogue_manifest_sha256=digest,
            capture_sources=sources,
        )
    observed = stage / "catalogue" if redirect == "child_directory" else foreign
    assert changed
    assert sorted(str(p.relative_to(observed)) for p in observed.rglob("*")) == [
        "user.txt"
    ]
    assert (observed / "user.txt").read_bytes() == b"preserve"
    assert not final.exists()


def test_retained_source_cannot_embed_unowned_authority_fields(
    catalogue_sources: Callable[..., dict[str, Any]],
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma import resource_catalogue
    from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
        NeotomaRetainedSource,
        capture_neotoma_resources,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.resources.protocol import (
        plan_from_json,
    )

    inputs = catalogue_sources()
    ancestors = inputs["resource_captures"]
    original = next(iter(ancestors.values()))
    plan, _ = plan_from_json(json.loads((original / "request-plan.json").read_bytes()))
    body = original / "dataset-202-current-attempt-1.body"
    checksum = sha256(body.read_bytes()).hexdigest()
    provenance = tmp_path / "retained-provenance.json"
    provenance.write_text(
        json.dumps(
            {
                "schema_version": "bokesjon-public-core-sources.v1",
                "sources": [
                    {
                        "source_url": "https://api.neotomadb.org/v2.0/data/downloads/202",
                        "final_url": "https://api.neotomadb.org/v2.0/data/downloads/202",
                        "status": 200,
                        "bytes": body.stat().st_size,
                        "sha256": checksum,
                        "retrieved_at": "2026-11-14T17:32:38.790438+00:00",
                    }
                ],
            }
        )
    )
    retained = {
        "dataset-202-current": NeotomaRetainedSource(
            body, provenance, sha256(provenance.read_bytes()).hexdigest(), checksum
        )
    }
    directory = tmp_path / "retained"
    captured = capture_neotoma_resources(
        directory,
        plan=plan,
        reuse_from=ancestors,
        retained_sources=retained,
        fetch=lambda *a, **k: pytest.fail("retained source GET"),
    )
    inputs.update(
        resource_captures={captured.manifest_sha256: directory},
        source_captures=ancestors,
        retained_sources=retained,
    )
    catalogue = resource_catalogue.build_neotoma_resource_catalogue(**inputs)
    sources = {
        **inputs["metadata_captures"],
        **inputs["resource_captures"],
        **ancestors,
    }
    publication = tmp_path / "public"
    resource_catalogue.write_neotoma_resource_catalogue(
        publication,
        catalogue=catalogue,
        capture_sources=sources,
        roster_path=inputs["roster_path"],
        retained_sources=retained,
    )
    digest = sha256((publication / "manifest.json").read_bytes()).hexdigest()
    output = tmp_path / "source-resources"
    api.write_neotoma_source_archive(
        output,
        catalogue_directory=publication,
        expected_catalogue_manifest_sha256=digest,
        capture_sources=sources,
        retained_sources=retained,
    )
    path = output / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest["retained_sources"]["dataset-202-current"]["scientific_admission"] = True
    path.write_text(json.dumps(manifest))
    pin = sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="retained.*fields"):
        api.load_neotoma_source_archive(output, expected_manifest_sha256=pin)


@pytest.mark.parametrize("nonempty", [False, True])
def test_archive_cannot_adopt_a_competing_root_at_writer_creation(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    nonempty: bool,
) -> None:
    catalogue, digest, sources = publish_catalogue(catalogue_sources())
    final = tmp_path / "source-resources"
    stage = tmp_path / ".source-resources.staging"
    foreign = tmp_path / "foreign-root"
    foreign.mkdir()
    if nonempty:
        (foreign / "user").write_bytes(b"preserve")
    original = OwnedTreeWriter
    changed = False

    def constructor(root: Path, **kwargs: Any) -> Any:
        nonlocal changed
        if root.exists():
            root.rename(tmp_path / "original-owned-root")
        foreign.rename(root)
        changed = True
        return original(root, **kwargs)

    monkeypatch.setattr(publication, "OwnedTreeWriter", constructor)
    with pytest.raises((ValueError, OSError)):
        api.write_neotoma_source_archive(
            final,
            catalogue_directory=catalogue,
            expected_catalogue_manifest_sha256=digest,
            capture_sources=sources,
        )
    assert changed and not final.exists()
    assert sorted(p.name for p in stage.iterdir()) == (["user"] if nonempty else [])
