"""Immutable context evidence remains separate from current-use native scope."""

from __future__ import annotations

from collections.abc import Callable
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from ...resource_catalogue.conftest import catalogue_sources as catalogue_sources
from ...resource_catalogue.reading.conftest import (
    publish_catalogue as publish_catalogue,
)
from ...resource_catalogue.reading.source_archive.original_metadata.conftest import (
    original_catalogue as original_catalogue,
)


@pytest.fixture
def context_inputs(
    catalogue_sources: Callable[..., dict[str, Any]],
    publish_catalogue: Callable[..., tuple[Path, str, dict[str, Path]]],
    tmp_path: Path,
) -> dict[str, Any]:
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
        write_neotoma_source_archive,
    )

    inputs = catalogue_sources()
    catalogue, pin, captures = publish_catalogue(inputs)
    native = tmp_path / "native"
    write_neotoma_source_archive(
        native,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=pin,
        capture_sources=captures,
    )
    authority = tmp_path / "authority.json"
    authority.write_bytes(b'{ "status": "observed_metadata_review", "rights": null }\n')
    legacy = tmp_path / "legacy.json"
    raw = inputs["roster_path"].read_bytes()
    legacy.write_bytes(b" \n" + raw + b"\n")
    return {
        "native_archive_directory": native,
        "expected_native_archive_sha256": sha256(
            (native / "manifest.json").read_bytes()
        ).hexdigest(),
        "legacy_rosters": {sha256(legacy.read_bytes()).hexdigest(): legacy},
        "exposure_authority": authority,
        "expected_exposure_authority_sha256": sha256(
            authority.read_bytes()
        ).hexdigest(),
    }


def test_context_preserves_original_buffers_and_scope_identity(
    context_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        load_neotoma_ancillary_context,
        write_neotoma_ancillary_context,
    )

    output = tmp_path / "context"
    manifest = write_neotoma_ancillary_context(output, **context_inputs)
    raw = (output / "manifest.json").read_bytes()
    loaded = load_neotoma_ancillary_context(
        output,
        expected_manifest_sha256=sha256(raw).hexdigest(),
        native_archive_directory=context_inputs["native_archive_directory"],
    )
    assert loaded.manifest == manifest
    assert len(manifest["files"]) == 2
    assert manifest["native_body_copies"] == 0
    assert manifest["pre_get_scope_reconstructed"] is False
    assert manifest["scientific_admission"] == "not_asserted"
    legacy_pin, legacy = next(iter(context_inputs["legacy_rosters"].items()))
    assert loaded.legacy_rosters[legacy_pin].read_bytes() == legacy.read_bytes()
    assert legacy_pin not in loaded.current_scope_inputs
    current = manifest["native_archive"]["current_roster_sha256"]
    assert set(loaded.current_scope_inputs) == {current}
    scope = loaded.current_scope_inputs[current]
    assert len(scope.metadata_captures) == 1
    assert scope.historical_metadata_parts == {}
    assert scope.alias_authority is None
    evidence = output / manifest["exposure_authority"]["path"]
    assert evidence.read_bytes() == context_inputs["exposure_authority"].read_bytes()
    assert json.loads(evidence.read_bytes())["status"] == "observed_metadata_review"
    assert (
        manifest["current_scope_verification"]
        == "resolver_identity_only_parent_obligations_not_replayed"
    )
    assert str(tmp_path) not in raw.decode()


def test_context_does_not_read_native_numerical_entities(
    context_inputs: dict[str, Any], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        load_neotoma_ancillary_context,
        write_neotoma_ancillary_context,
    )

    original = Path.open
    native = context_inputs["native_archive_directory"]

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.is_relative_to(native) and path.suffix == ".body":
            raise AssertionError(f"Unselected native entity opened: {path}")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", observed)
    output = tmp_path / "context"
    write_neotoma_ancillary_context(output, **context_inputs)
    load_neotoma_ancillary_context(
        output,
        expected_manifest_sha256=sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        native_archive_directory=native,
    )


def test_existing_destination_is_preserved(
    context_inputs: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        write_neotoma_ancillary_context,
    )

    output = tmp_path / "context"
    output.mkdir()
    witness = output / "user"
    witness.write_bytes(b"owned by another writer")
    with pytest.raises(FileExistsError):
        write_neotoma_ancillary_context(output, **context_inputs)
    assert witness.read_bytes() == b"owned by another writer"


@pytest.mark.parametrize("incomplete", [False, True])
def test_historical_metadata_is_internal_and_required(
    original_catalogue: tuple[Path, str, dict[str, Path], Path],
    tmp_path: Path,
    incomplete: bool,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        load_neotoma_ancillary_context,
        write_neotoma_ancillary_context,
    )
    from bijux_pollenomics.collection.sources.neotoma.resource_catalogue.archive import (
        write_neotoma_source_archive,
    )

    catalogue, digest, sources, original = original_catalogue
    native = tmp_path / "native"
    write_neotoma_source_archive(
        native,
        catalogue_directory=catalogue,
        expected_catalogue_manifest_sha256=digest,
        capture_sources=sources,
        original_relational_root=original,
    )
    original.rename(tmp_path / "detached-external")
    if incomplete:
        (native / "captures/original-metadata/surfaces/datasets/201.json").unlink()
    roster = catalogue / "source-inventory.json"
    roster_pin = sha256(roster.read_bytes()).hexdigest()
    authority = tmp_path / "authority.json"
    authority.write_bytes(b'{"status":"literal_source_review"}')
    output = tmp_path / "context"
    kwargs: dict[str, Any] = {
        "native_archive_directory": native,
        "expected_native_archive_sha256": sha256(
            (native / "manifest.json").read_bytes()
        ).hexdigest(),
        "legacy_rosters": {roster_pin: roster},
        "exposure_authority": authority,
        "expected_exposure_authority_sha256": sha256(
            authority.read_bytes()
        ).hexdigest(),
    }
    if incomplete:
        with pytest.raises(ValueError):
            write_neotoma_ancillary_context(output, **kwargs)
        assert not output.exists()
        return
    write_neotoma_ancillary_context(output, **kwargs)
    loaded = load_neotoma_ancillary_context(
        output,
        expected_manifest_sha256=sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        native_archive_directory=native,
    )
    scope = loaded.current_scope_inputs[roster_pin]
    assert len(scope.metadata_captures) == 2
    assert scope.historical_metadata_parts is not None
    assert len(scope.historical_metadata_parts) == 1
    assert all(
        path.is_relative_to(native) for path in scope.historical_metadata_parts.values()
    )
