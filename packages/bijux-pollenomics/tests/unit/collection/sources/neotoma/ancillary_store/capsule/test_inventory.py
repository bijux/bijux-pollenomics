"""Metadata inventory verifies nonbody joins while leaving entity buffers unopened."""

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


def _context_resolvers(inputs: dict[str, Any]) -> dict[str, Any]:
    return {
        key: inputs[key] for key in ("context_directory", "native_archive_directory")
    }


def test_inventory_is_body_free_and_preserves_exact_source_occurrences(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        load_neotoma_ancillary_capsule,
        read_neotoma_ancillary_capsule_inventory,
        write_neotoma_ancillary_capsule,
    )

    output = tmp_path / "capsule"
    write_neotoma_ancillary_capsule(output, **capsule_inputs)
    pin = sha256((output / "manifest.json").read_bytes()).hexdigest()
    kwargs = _context_resolvers(capsule_inputs)
    full = load_neotoma_ancillary_capsule(
        output, expected_manifest_sha256=pin, **kwargs
    )
    roots = {
        output,
        *capsule_inputs["facet_captures"].values(),
        *capsule_inputs["linked_captures"].values(),
    }
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and any(path.is_relative_to(root) for root in roots):
            pytest.fail("Metadata inventory opened a facet/linked entity body")
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    metadata = read_neotoma_ancillary_capsule_inventory(
        output, expected_manifest_sha256=pin, **kwargs
    )
    assert metadata.manifest == full.manifest
    assert metadata.index == full.index
    assert metadata.entity_body_hashes_verified is False
    assert metadata.source_assessments_replayed is False
    assert metadata.integrity_scope == "capsule_metadata_and_source_declarations"


def test_same_length_body_change_is_explicitly_unverified_until_full_replay(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        load_neotoma_ancillary_capsule,
        read_neotoma_ancillary_capsule_inventory,
        write_neotoma_ancillary_capsule,
    )

    output = tmp_path / "capsule"
    write_neotoma_ancillary_capsule(output, **capsule_inputs)
    pin = sha256((output / "manifest.json").read_bytes()).hexdigest()
    body = next((output / "captures").glob("*/*.body"))
    before = body.read_bytes()
    body.write_bytes(b"x" * len(before))
    kwargs = _context_resolvers(capsule_inputs)
    assert (
        read_neotoma_ancillary_capsule_inventory(
            output, expected_manifest_sha256=pin, **kwargs
        ).entity_body_hashes_verified
        is False
    )
    with pytest.raises(ValueError):
        load_neotoma_ancillary_capsule(output, expected_manifest_sha256=pin, **kwargs)


@pytest.mark.parametrize(
    "mutation", ["index", "receipt", "plan", "proof", "extra", "size", "rehashed_index"]
)
def test_inventory_refuses_nonbody_or_closed_namespace_changes_before_body_access(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        read_neotoma_ancillary_capsule_inventory,
        write_neotoma_ancillary_capsule,
    )

    output = tmp_path / "capsule"
    manifest = write_neotoma_ancillary_capsule(output, **capsule_inputs)
    if mutation in {"index", "rehashed_index"}:
        path = output / "index.json"
        document = json.loads(path.read_bytes())
        document["observations"][0]["terminal_status"] = "scientifically_admitted"
        path.write_text(json.dumps(document))
        if mutation == "rehashed_index":
            member = manifest["files"]["index.json"]
            manifest["source_bytes"] += path.stat().st_size - member["bytes"]
            member.update(
                sha256=sha256(path.read_bytes()).hexdigest(), bytes=path.stat().st_size
            )
            (output / "manifest.json").write_text(json.dumps(manifest))
    elif mutation == "extra":
        (output / "foreign").mkdir()
    elif mutation == "size":
        next((output / "captures").glob("*/*.body")).write_bytes(b"foreign")
    else:
        pattern = {
            "receipt": "*/*.receipt.json",
            "plan": "*/request-plan.json",
            "proof": "*/parent-scope.json",
        }[mutation]
        path = next((output / "captures").glob(pattern))
        path.write_bytes(b"x" * path.stat().st_size)
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.is_relative_to(output) and path.suffix == ".body":
            pytest.fail("Inventory read an entity before nonbody refusal")
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    with pytest.raises(ValueError):
        read_neotoma_ancillary_capsule_inventory(
            output,
            expected_manifest_sha256=sha256(
                (output / "manifest.json").read_bytes()
            ).hexdigest(),
            **_context_resolvers(capsule_inputs),
        )


def test_linked_inventory_checks_only_predecessor_metadata(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        read_neotoma_ancillary_capsule_inventory,
        write_neotoma_ancillary_capsule,
    )

    source = next(iter(capsule_inputs["facet_captures"]))
    predecessors = {source: capsule_inputs["facet_captures"][source]}
    capsule_inputs["facet_captures"] = {}
    output = tmp_path / "capsule"
    write_neotoma_ancillary_capsule(
        output, predecessor_facets=predecessors, **capsule_inputs
    )
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.suffix == ".body" and (
            path.is_relative_to(output) or path.is_relative_to(predecessors[source])
        ):
            pytest.fail("Linked inventory opened predecessor or linked body")
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    loaded = read_neotoma_ancillary_capsule_inventory(
        output,
        expected_manifest_sha256=sha256(
            (output / "manifest.json").read_bytes()
        ).hexdigest(),
        predecessor_facets=predecessors,
        **_context_resolvers(capsule_inputs),
    )
    assert len(loaded.index["observations"]) == 1
    assert loaded.manifest["predecessor_facets"] == [source]


def _rebind_metadata(output: Path, old: str, *, request_count: bool = False) -> str:
    manifest = json.loads((output / "manifest.json").read_bytes())
    directory = output / "captures" / old
    digest = sha256((directory / "capture-manifest.json").read_bytes()).hexdigest()
    renamed = directory.with_name(digest)
    directory.rename(renamed)
    descriptor = manifest["captures"].pop(old)
    manifest["captures"][digest] = descriptor
    files = {
        name.replace(f"captures/{old}/", f"captures/{digest}/"): member
        for name, member in manifest["files"].items()
    }
    for name, member in descriptor["files"].items():
        if not name.endswith(".body"):
            raw = (renamed / name).read_bytes()
            member.update(sha256=sha256(raw).hexdigest(), bytes=len(raw))
        files[f"captures/{digest}/{name}"] = dict(member)
    path = output / "index.json"
    index = json.loads(path.read_text().replace(old, digest))
    if request_count:
        next(
            row
            for row in index["captures"]
            if row["source_capture_manifest_sha256"] == digest
        )["request_count"] += 1
    index["captures"].sort(key=lambda row: row["source_capture_manifest_sha256"])
    index["observations"].sort(
        key=lambda row: (
            row["source_capture_manifest_sha256"],
            int(row["source_entry_pointer"].rsplit("/", 1)[1]),
        )
    )
    raw = (
        json.dumps(index, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()
    path.write_bytes(raw)
    files["index.json"] = {"sha256": sha256(raw).hexdigest(), "bytes": len(raw)}
    manifest["files"] = files
    manifest["source_bytes"] = sum(member["bytes"] for member in files.values())
    (output / "manifest.json").write_text(json.dumps(manifest))
    return sha256((output / "manifest.json").read_bytes()).hexdigest()


@pytest.mark.parametrize(
    "mutation", ["source_count", "parent_proof", "closed_status", "scientific_claim"]
)
def test_rehashed_source_metadata_cannot_fabricate_counts_or_parent_proofs(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        read_neotoma_ancillary_capsule_inventory,
        write_neotoma_ancillary_capsule,
    )

    capsule_inputs["linked_captures"] = {}
    output = tmp_path / "capsule"
    manifest = write_neotoma_ancillary_capsule(output, **capsule_inputs)
    scoped = mutation == "parent_proof"
    digest = next(
        pin
        for pin, record in manifest["captures"].items()
        if ("scoped" in record["native_schema_version"]) == scoped
    )
    source = output / "captures" / digest
    path = source / "capture-manifest.json"
    document = json.loads(path.read_bytes())
    if mutation == "source_count":
        document["request_count"] += 1
    elif mutation == "closed_status":
        document["status"] = "invented_source_state"
    elif mutation == "scientific_claim":
        document["scientific_admission"] = "approved"
    else:
        proof_path = source / "parent-scope.json"
        proof = json.loads(proof_path.read_bytes())
        proof["parents"][0]["effective_scope_role"] = "heldout_no_numerical_access"
        proof_path.write_text(json.dumps(proof))
        control_path = source / "request-plan.json"
        control = json.loads(control_path.read_bytes())
        control["parent_scope"]["sha256"] = sha256(proof_path.read_bytes()).hexdigest()
        control_path.write_text(json.dumps(control))
        document["plan_sha256"] = sha256(control_path.read_bytes()).hexdigest()
    path.write_text(json.dumps(document))
    pin = _rebind_metadata(output, digest, request_count=mutation == "source_count")
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.is_relative_to(output) and path.suffix == ".body":
            pytest.fail("Metadata forgery probe opened a numerical entity")
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    with pytest.raises(ValueError):
        read_neotoma_ancillary_capsule_inventory(
            output,
            expected_manifest_sha256=pin,
            **_context_resolvers(capsule_inputs),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("root_dataset_id", 999),
        ("native_id", 2),
        ("source_receipt_sha256", "0" * 64),
        ("source_body_sha256", "0" * 64),
        ("inherited_exposure_role", "heldout_no_numerical_access"),
        ("json_pointer", 42),
    ],
)
def test_rehashed_linked_occurrences_must_match_predecessor_metadata(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: Any,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        read_neotoma_ancillary_capsule_inventory,
        write_neotoma_ancillary_capsule,
    )

    output = tmp_path / "capsule"
    manifest = write_neotoma_ancillary_capsule(output, **capsule_inputs)
    digest = next(
        pin
        for pin, record in manifest["captures"].items()
        if record["kind"] == "linked"
    )
    source = output / "captures" / digest
    control_path = source / "request-plan.json"
    control = json.loads(control_path.read_bytes())
    document_path = source / "capture-manifest.json"
    document = json.loads(document_path.read_bytes())
    control["targets"][0]["source_proofs"][0][field] = value
    document["resources"][0]["identity"]["source_proofs"][0][field] = value
    control_path.write_text(json.dumps(control))
    document["plan_sha256"] = sha256(control_path.read_bytes()).hexdigest()
    document_path.write_text(json.dumps(document))
    index_path = output / "index.json"
    index = json.loads(index_path.read_bytes())
    next(row for row in index["observations"] if row["kind"] == "linked")[
        "identity"
    ] = document["resources"][0]["identity"]
    index_path.write_text(json.dumps(index))
    pin = _rebind_metadata(output, digest)
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.is_relative_to(output) and path.suffix == ".body":
            pytest.fail("Linked occurrence metadata check opened an entity body")
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    with pytest.raises(ValueError):
        read_neotoma_ancillary_capsule_inventory(
            output,
            expected_manifest_sha256=pin,
            **_context_resolvers(capsule_inputs),
        )


@pytest.mark.parametrize(
    "field,value,receipt_status",
    [
        ("requested_url", "https://foreign.invalid/", None),
        ("tls_mode", "unverified", None),
        ("utc_end", "1900-01-01T00:00:00+00:00", None),
        ("http_status", True, None),
        ("http_status", 404, None),
        ("body_complete", False, None),
        ("http_status", 404, "refused_http_response"),
        ("body_complete", False, "refused_http_response"),
    ],
)
def test_rehashed_receipt_metadata_keeps_route_tls_timing_and_scalar_identity(
    capsule_inputs: dict[str, Any],
    tmp_path: Path,
    field: str,
    value: Any,
    receipt_status: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule import (
        read_neotoma_ancillary_capsule_inventory,
        write_neotoma_ancillary_capsule,
    )

    capsule_inputs["linked_captures"] = {}
    output = tmp_path / "capsule"
    manifest = write_neotoma_ancillary_capsule(output, **capsule_inputs)
    digest = next(
        pin
        for pin, record in manifest["captures"].items()
        if "scoped" not in record["native_schema_version"]
    )
    source = output / "captures" / digest
    path = source / "capture-manifest.json"
    document = json.loads(path.read_bytes())
    entry = next(row for row in document["facets"] if row["attempts"])
    attempt = entry["attempts"][-1]
    receipt_path = source / attempt["receipt_file"]
    receipt = json.loads(receipt_path.read_bytes())
    receipt[field] = value
    if receipt_status is not None:
        receipt["terminal_status"] = receipt_status
    receipt_path.write_text(json.dumps(receipt))
    attempt["receipt_sha256"] = sha256(receipt_path.read_bytes()).hexdigest()
    path.write_text(json.dumps(document))
    index_path = output / "index.json"
    index = json.loads(index_path.read_bytes())
    row = next(
        row
        for row in index["observations"]
        if row["source_capture_manifest_sha256"] == digest
        and row["facet_key"] == entry["facet_key"]
    )
    row["attempts"][-1]["receipt_sha256"] = attempt["receipt_sha256"]
    index_path.write_text(json.dumps(index))
    pin = _rebind_metadata(output, digest)
    original = capture_opening()

    def observed(path: Path, *args: Any, **kwargs: Any) -> Any:
        if path.is_relative_to(output) and path.suffix == ".body":
            pytest.fail("Contradictory receipt metadata opened an entity body")
        return original(path, *args, **kwargs)

    observe_opening(monkeypatch, observed)
    with pytest.raises(ValueError):
        read_neotoma_ancillary_capsule_inventory(
            output,
            expected_manifest_sha256=pin,
            **_context_resolvers(capsule_inputs),
        )


@pytest.mark.parametrize(
    "http_status,complete,outcome",
    [(404, True, "unavailable_http"), (200, False, "refused_incomplete_body")],
)
def test_consistent_declared_http_failures_remain_valid_metadata(
    capsule_inputs: dict[str, Any],
    http_status: int,
    complete: bool,
    outcome: str,
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.ancillary_store.capsule.models import (
        verify_receipt_metadata,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.facets.protocol import (
        plan_from_json,
        request_for,
    )
    from bijux_pollenomics.collection.sources.neotoma.capture.receipts import _utc

    source = next(iter(capsule_inputs["facet_captures"].values()))
    manifest = json.loads((source / "capture-manifest.json").read_bytes())
    control = json.loads((source / "request-plan.json").read_bytes())
    plan, _ = plan_from_json(control)
    entry = next(row for row in manifest["facets"] if row["attempts"])
    resource = next(
        row
        for row in plan.resources
        if row.dataset_id == entry["root_identity"]["dataset_id"]
    )
    request = request_for(resource, entry["facet"], 1)
    receipt = json.loads((source / entry["attempts"][0]["receipt_file"]).read_bytes())
    receipt.update(
        http_status=http_status,
        body_complete=complete,
        terminal_status="refused_http_response",
    )
    entry["terminal_status"] = outcome
    assert verify_receipt_metadata(
        receipt, request, manifest, _utc(manifest["capture_utc_start"])
    ) == _utc(receipt["utc_end"])
