"""Derived current qualification authenticates immutable acquisition and ancestry."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture import NeotomaMetadataResponse
from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _read
from bijux_pollenomics.collection.sources.neotoma.capture.resources import (
    NeotomaResourcePlan,
    capture_neotoma_resources,
    replay_neotoma_resource_capture,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.current import (
    qualification as owner,
)
from bijux_pollenomics.collection.sources.neotoma.capture.resources.current import (
    qualify_neotoma_current_capture,
)

from .native_payloads import payload, resource


def capture(
    directory: Path,
    *,
    kind: str = "testate amoebae surface sample",
    role: str = "development_resource_discovery",
    status: int = 200,
    empty: bool = False,
) -> Any:
    spec = resource(kind, exposure_role=role)
    source = payload(spec)
    if empty:
        source["data"] = []
    body = json.dumps(source).encode()

    def fetch(url: str, **_kwargs: Any) -> NeotomaMetadataResponse:
        assert role == "development_resource_discovery", "Protected body fetched"
        return NeotomaMetadataResponse(
            url, status, (("Content-Length", str(len(body))),), body
        )

    return capture_neotoma_resources(
        directory, plan=NeotomaResourcePlan((spec,), "b" * 64), fetch=fetch
    )


def test_qualification_adds_source_profile_without_relabelling_original_capture(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "source"
    acquired = capture(directory)
    assert acquired.resources[0]["terminal_status"] == "unsupported_dataset_type"
    files = {p.name: sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()}
    result = qualify_neotoma_current_capture(
        directory, expected_manifest_sha256=acquired.manifest_sha256
    )
    assert result["source_capture_relabelled"] is False
    row = result["resources"][0]
    assert row["source_terminal_status"] == "unsupported_dataset_type"
    assert row["qualification_status"] == "parsed_current_source"
    assert row["source"]["capture_manifest_sha256"] == acquired.manifest_sha256
    assert row["summary"]["source_units"] == ["NISP", "cm", "per mille"]
    assert row["summary"]["biological_denominator"] == "not_established"
    assert row["summary"]["physical_depth_or_chronology_inferred"] is False
    context = next(
        c
        for c in row["summary"]["native_contexts"]
        if c["variablename"] == "water table depth"
    )
    assert context["element"] is None and context["units"] == "cm"
    assert files == {
        p.name: sha256(p.read_bytes()).hexdigest() for p in directory.iterdir()
    }
    assert (
        replay_neotoma_resource_capture(
            directory, expected_manifest_sha256=acquired.manifest_sha256
        )
        == acquired
    )


def test_reused_source_retains_its_original_http_epoch_and_pointer(
    tmp_path: Path,
) -> None:
    original = tmp_path / "original"
    acquired = capture(original)

    def never(*_args: Any, **_kwargs: Any) -> Any:
        raise AssertionError("Reused source contacted HTTP")

    reused = tmp_path / "reused"
    capture_result = capture_neotoma_resources(
        reused,
        plan=NeotomaResourcePlan((resource(),), "b" * 64),
        reuse_from={acquired.manifest_sha256: original},
        fetch=never,
    )
    assert capture_result.request_count == 0
    result = qualify_neotoma_current_capture(
        reused,
        expected_manifest_sha256=capture_result.manifest_sha256,
        source_captures={acquired.manifest_sha256: original},
    )
    row = result["resources"][0]
    assert row["qualification_status"] == "parsed_current_source"
    assert row["source"]["capture_manifest_sha256"] == acquired.manifest_sha256
    reference = acquired.resources[0]["attempts"][0]
    receipt = json.loads((original / reference["receipt_file"]).read_bytes())
    assert row["source"]["receipt_sha256"] == reference["receipt_sha256"]
    assert row["source"]["body_sha256"] == receipt["retained_body_sha256"]
    assert row["source"]["utc_start"] == receipt["utc_start"]


@pytest.mark.parametrize(
    "role", ["reserved_candidate_confirmation", "heldout_no_numerical_access"]
)
def test_protected_qualification_never_reads_source_entities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role: str
) -> None:
    directory = tmp_path / "protected"
    acquired = capture(directory, role=role)
    original_read = _read

    def guarded(path: Path, bound: int) -> bytes:
        assert path.suffix != ".body", "Protected source entity opened"
        return original_read(path, bound)

    monkeypatch.setattr(owner, "_read", guarded)
    result = qualify_neotoma_current_capture(
        directory, expected_manifest_sha256=acquired.manifest_sha256
    )
    assert (
        result["resources"][0]["qualification_status"] == "not_qualified_exposure_role"
    )
    assert "source" not in result["resources"][0]


@pytest.mark.parametrize(
    ("kind", "status", "empty", "expected"),
    [
        ("unobserved native proxy", 200, False, "not_qualified_dataset_type"),
        ("pollen", 200, False, "not_applicable_existing_native_profile"),
        ("speleothem", 404, False, "not_qualified_source_result"),
        ("speleothem", 200, True, "unavailable_current_api_empty"),
    ],
)
def test_profile_scope_and_source_unavailability_are_explicit(
    tmp_path: Path, kind: str, status: int, empty: bool, expected: str
) -> None:
    directory = tmp_path / "source"
    acquired = capture(directory, kind=kind, status=status, empty=empty)
    result = qualify_neotoma_current_capture(
        directory, expected_manifest_sha256=acquired.manifest_sha256
    )
    assert result["resources"][0]["qualification_status"] == expected
    assert result["resources"][0]["scientific_admission"] == "not_asserted"
    if empty:
        assert result["resources"][0]["absence_certified"] is False


def test_changed_actual_buffer_after_acquisition_replay_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "source"
    acquired = capture(directory)
    original_read = _read

    def different(path: Path, bound: int) -> bytes:
        content = original_read(path, bound)
        if path.suffix == ".body":
            changed = json.loads(content)
            changed["data"][0]["site"]["collectionunit"]["dataset"]["samples"][0][
                "datum"
            ][0]["value"] = 999
            return json.dumps(changed).encode()
        return content

    monkeypatch.setattr(owner, "_read", different)
    with pytest.raises(ValueError, match="identity|receipt"):
        qualify_neotoma_current_capture(
            directory, expected_manifest_sha256=acquired.manifest_sha256
        )


def test_frozen_entities_never_receive_a_current_source_qualification(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "frozen"
    spec = replace(resource(), versions=("doi_frozen",))
    body = json.dumps(payload(spec)).encode()
    acquired = capture_neotoma_resources(
        directory,
        plan=NeotomaResourcePlan((spec,), "b" * 64),
        fetch=lambda url, **_kwargs: NeotomaMetadataResponse(
            url, 200, (("Content-Length", str(len(body))),), body
        ),
    )
    result = qualify_neotoma_current_capture(
        directory, expected_manifest_sha256=acquired.manifest_sha256
    )
    assert result["resources"] == []


def test_qualification_refuses_wrong_independent_manifest_anchor(
    tmp_path: Path,
) -> None:
    directory = tmp_path / "source"
    capture(directory)
    with pytest.raises(ValueError, match="manifest"):
        qualify_neotoma_current_capture(directory, expected_manifest_sha256="0" * 64)
