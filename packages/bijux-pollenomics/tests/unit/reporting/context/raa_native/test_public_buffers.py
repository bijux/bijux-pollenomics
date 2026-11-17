"""Retain the public curation and profile-binding contract for constructed buffers."""

import json
from pathlib import Path

import pytest

from bijux_pollenomics.reporting.context.raa_native import NativeRegistryContextSnapshot
from bijux_pollenomics.reporting.context.raa_native.publication import (
    publish_native_registry_context,
)
from tests.unit.reporting.context.raa_native.test_snapshot import (
    capture,
    generated_inputs,
)


@pytest.mark.parametrize(
    "mutation", ["nested-private-ledger", "false-independent-profile"]
)
def test_constructed_public_snapshot_refuses_uncurated_nested_metadata(
    tmp_path: Path, mutation: str
) -> None:
    inputs = tmp_path / "generated-aggregate"
    generated_inputs(inputs)
    snapshot = capture(inputs)
    context = json.loads(snapshot.context_bytes)
    if mutation == "nested-private-ledger":
        context["counts"]["private_uuid_ledger"] = ["GENERATED-PRIVATE-ROW-MARKER"]
    else:
        context["native_profile_binding"]["scope"] = (
            "independently reconstructed complete national profile"
        )
    forged = NativeRegistryContextSnapshot(
        json.dumps(context).encode(), snapshot.counts_bytes, snapshot.cells_bytes
    )
    output = tmp_path / "public-output"
    output.mkdir()
    with pytest.raises(ValueError):
        publish_native_registry_context(forged, output_dir=output)
    assert not (output / "context").exists()


@pytest.mark.parametrize(
    "mutation",
    ["private-input-field", "boolean-input-size", "false-source-verification"],
)
def test_public_input_and_verification_records_are_exact(
    tmp_path: Path, mutation: str
) -> None:
    generated_inputs(tmp_path / "input")
    snapshot = capture(tmp_path / "input")
    context = json.loads(snapshot.context_bytes)
    if mutation == "private-input-field":
        context["inputs"]["report.json"]["private_path"] = "GENERATED-PRIVATE-PATH"
    elif mutation == "boolean-input-size":
        context["inputs"]["report.json"]["byte_count"] = True
    else:
        context["source_verification"] = "fresh original national replay"
    forged = NativeRegistryContextSnapshot(
        json.dumps(context).encode(), snapshot.counts_bytes, snapshot.cells_bytes
    )
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(ValueError):
        publish_native_registry_context(forged, output_dir=output)
    assert not (output / "context").exists()


def test_duplicate_public_json_keys_refuse_before_output(tmp_path: Path) -> None:
    generated_inputs(tmp_path / "input")
    snapshot = capture(tmp_path / "input")
    duplicate = snapshot.context_bytes.replace(
        b'"counts":',
        b'"counts":{"private_uuid_ledger":["GENERATED-PRIVATE-ROW-MARKER"]},"counts":',
        1,
    )
    forged = NativeRegistryContextSnapshot(
        duplicate, snapshot.counts_bytes, snapshot.cells_bytes
    )
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(ValueError):
        publish_native_registry_context(forged, output_dir=output)
    assert not (output / "context").exists()
