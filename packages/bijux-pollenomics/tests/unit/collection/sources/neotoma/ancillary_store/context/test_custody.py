"""Context custody refuses rehashed claims and unowned filesystem members."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from tests.unit.collection.sources.neotoma.reading_observation import (
    capture_opening,
    observe_opening,
)


@pytest.mark.parametrize(
    "mutation", ["extra", "empty_directory", "symlink", "hardlink", "evidence"]
)
def test_context_closed_namespace_and_evidence(
    context_inputs: dict[str, Any], tmp_path: Path, mutation: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        load_neotoma_ancillary_context,
        write_neotoma_ancillary_context,
    )

    output = tmp_path / "context"
    manifest = write_neotoma_ancillary_context(output, **context_inputs)
    pin = sha256((output / "manifest.json").read_bytes()).hexdigest()
    evidence = output / manifest["exposure_authority"]["path"]
    if mutation == "extra":
        (output / "foreign").write_bytes(b"foreign")
    elif mutation == "empty_directory":
        (output / "foreign").mkdir()
    elif mutation == "symlink":
        evidence.unlink()
        evidence.symlink_to(context_inputs["exposure_authority"])
    elif mutation == "hardlink":
        import os

        os.link(evidence, tmp_path / "foreign-hardlink")
    else:
        evidence.write_bytes(b"{}")
    with pytest.raises(ValueError):
        load_neotoma_ancillary_context(
            output,
            expected_manifest_sha256=pin,
            native_archive_directory=context_inputs["native_archive_directory"],
        )


@pytest.mark.parametrize(
    "mutation",
    ["scope", "native", "metadata", "historical", "unowned_file", "claim", "kind"],
)
def test_rehashed_context_cannot_change_source_or_scientific_claims(
    context_inputs: dict[str, Any], tmp_path: Path, mutation: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        load_neotoma_ancillary_context,
        write_neotoma_ancillary_context,
    )

    output = tmp_path / "context"
    manifest = write_neotoma_ancillary_context(output, **context_inputs)
    if mutation == "scope":
        next(iter(manifest["legacy_rosters"].values()))["use_scope"] = "current_scope"
    elif mutation == "native":
        manifest["native_archive"]["manifest_sha256"] = "0" * 64
    elif mutation == "metadata":
        manifest["native_archive"]["metadata_capture_manifest_sha256s"] = []
    elif mutation == "historical":
        manifest["native_archive"]["historical_metadata_part_sha256s"] = ["0" * 64]
    elif mutation == "unowned_file":
        raw = b"{}"
        (output / "foreign.json").write_bytes(raw)
        manifest["files"]["foreign.json"] = {
            "bytes": 2,
            "sha256": sha256(raw).hexdigest(),
        }
        manifest["source_bytes"] += 2
    elif mutation == "kind":
        manifest["native_body_copies"] = False
    else:
        manifest["scientific_admission"] = "approved"
    raw = json.dumps(manifest).encode()
    (output / "manifest.json").write_bytes(raw)
    with pytest.raises(ValueError):
        load_neotoma_ancillary_context(
            output,
            expected_manifest_sha256=sha256(raw).hexdigest(),
            native_archive_directory=context_inputs["native_archive_directory"],
        )


@pytest.mark.parametrize(
    "input_name",
    ["expected_native_archive_sha256", "expected_exposure_authority_sha256"],
)
def test_incorrect_input_identity_never_publishes(
    context_inputs: dict[str, Any], tmp_path: Path, input_name: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        write_neotoma_ancillary_context,
    )

    context_inputs[input_name] = "0" * 64
    output = tmp_path / "context"
    with pytest.raises(ValueError):
        write_neotoma_ancillary_context(output, **context_inputs)
    assert not output.exists()


@pytest.mark.parametrize(
    "mutation", ["population", "identity", "role", "database", "policy"]
)
def test_malformed_legacy_roster_refuses_even_with_matching_digest(
    context_inputs: dict[str, Any], tmp_path: Path, mutation: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        write_neotoma_ancillary_context,
    )

    path = next(iter(context_inputs["legacy_rosters"].values()))
    roster = json.loads(path.read_bytes())
    if mutation == "population":
        roster["resource_count"] = True
    elif mutation == "identity":
        roster["resources"][0]["dataset_id"] = True
    elif mutation == "role":
        roster["resources"][0]["exposure_roles"]["current"] = "development"
    elif mutation == "database":
        del roster["resources"][0]["database"]
    else:
        roster["policy_sources"] = []
    raw = json.dumps(roster).encode()
    path.write_bytes(raw)
    context_inputs["legacy_rosters"] = {sha256(raw).hexdigest(): path}
    output = tmp_path / "context"
    with pytest.raises(ValueError):
        write_neotoma_ancillary_context(output, **context_inputs)
    assert not output.exists()


@pytest.mark.parametrize("budget", ["bytes", "files"])
def test_context_finite_budgets_refuse_before_legacy_buffer(
    context_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    budget: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.context import (
        publication,
    )

    legacy = next(iter(context_inputs["legacy_rosters"].values()))
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path == legacy:
            pytest.fail("Over-budget legacy input buffer opened")
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    monkeypatch.setattr(
        publication,
        "MAX_BYTES" if budget == "bytes" else "MAX_FILES",
        128 if budget == "bytes" else 2,
    )
    output = tmp_path / "context"
    with pytest.raises(ValueError):
        publication.write_neotoma_ancillary_context(output, **context_inputs)
    assert not output.exists()


def test_loader_hashes_and_validates_each_copied_evidence_buffer_once(
    context_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store import (
        load_neotoma_ancillary_context,
        write_neotoma_ancillary_context,
    )

    output = tmp_path / "context"
    manifest = write_neotoma_ancillary_context(output, **context_inputs)
    files = {output / name: 0 for name in manifest["files"]}
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path in files:
            files[path] += 1
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    load_neotoma_ancillary_context(
        output,
        expected_manifest_sha256=sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        native_archive_directory=context_inputs["native_archive_directory"],
    )
    assert set(files.values()) == {1}
