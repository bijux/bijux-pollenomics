"""Replay source-owned SEAD normalization against every admitted logical document."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.sead.acquisition.admission import (
    SeadAdmissionExpectedIdentity,
)
from bijux_pollenomics.collection.sources.sead.evidence.bundle import (
    build_sead_source_native_evidence_bundle,
    validate_sead_source_native_evidence_materialization,
)

from ..models import SourceRow, canonical_bytes
from ..reading import checked_directory, evidence_inventory, json_object


@dataclass(frozen=True)
class SeadEvidence:
    """Verified input identities; logical rows are read a bounded part at a time."""

    raw_root: Path
    normalized_root: Path
    boundary_root: Path
    inventories: tuple[tuple[str, tuple[tuple[str, str], ...]], ...]
    manifest_bytes: bytes
    replay_receipt_bytes: bytes

    def roots(self) -> dict[str, Path]:
        return {
            "raw": self.raw_root,
            "normalized": self.normalized_root,
            "country_authority": self.boundary_root,
        }

    def assert_unchanged(self) -> None:
        for authority, records in self.inventories:
            if evidence_inventory(self.roots()[authority]) != records:
                raise ValueError(f"SEAD {authority} evidence changed during audit")

    def input_records(self) -> list[dict[str, str]]:
        return [
            {"authority": authority, "path": path, "sha256": digest}
            for authority, records in self.inventories
            for path, digest in records
        ]

    def manifest(self) -> dict[str, Any]:
        return json_object(self.manifest_bytes)

    def document(self, name: str) -> dict[str, Any]:
        records = dict(dict(self.inventories)["normalized"])
        if name not in records:
            raise ValueError("SEAD logical document is outside the admitted inventory")
        content = (self.normalized_root / name).read_bytes()
        if hashlib.sha256(content).hexdigest() != records[name]:
            raise ValueError("SEAD logical document changed")
        return json_object(content)

    def rows(self, document: str, field: str) -> Iterator[SourceRow]:
        index = self.document(document)
        if field in index:
            for row_index, row in enumerate(index[field]):
                yield SourceRow(
                    f"{document}:{field}", document, row_index, canonical_bytes(row)
                )
            return
        records = dict(dict(self.inventories)["normalized"])
        for part in index["partitioned_fields"][field]["parts"]:
            path = part["path"]
            content = (self.normalized_root / path).read_bytes()
            if hashlib.sha256(content).hexdigest() != records[path]:
                raise ValueError("SEAD normalized part changed")
            values = json_object(content)[field]
            if len(values) != part["row_count"]:
                raise ValueError("SEAD normalized part denominator changed")
            for row_index, row in enumerate(values):
                yield SourceRow(
                    f"{document}:{field}", path, row_index, canonical_bytes(row)
                )

    def raw_rows(self, table: str) -> list[dict[str, Any]]:
        path = f"payloads/{table}.json"
        records = dict(dict(self.inventories)["raw"])
        if path not in records:
            raise ValueError("SEAD raw table is outside the admitted inventory")
        content = (self.raw_root / path).read_bytes()
        if hashlib.sha256(content).hexdigest() != records[path]:
            raise ValueError("SEAD raw table changed")
        return list(json_object(content)["rows"])


def read_sead_evidence(
    raw_root: Path,
    normalized_root: Path,
    *,
    expected_identity: SeadAdmissionExpectedIdentity,
) -> SeadEvidence:
    raw, normalized, boundary = (
        checked_directory(path)
        for path in (
            raw_root,
            normalized_root,
            expected_identity.country_authority_root,
        )
    )
    if raw.is_relative_to(normalized) or normalized.is_relative_to(raw):
        raise ValueError("SEAD raw and normalized authorities must be disjoint")
    roots = {"raw": raw, "normalized": normalized, "country_authority": boundary}
    inventories = tuple(
        (name, evidence_inventory(root)) for name, root in roots.items()
    )
    manifest_bytes = (
        normalized / "evidence_materialization_manifest.json"
    ).read_bytes()
    manifest = validate_sead_source_native_evidence_materialization(normalized)
    if canonical_bytes(manifest) != manifest_bytes:
        raise ValueError("SEAD normalized manifest changed during validation")
    evidence = SeadEvidence(
        raw, normalized, boundary, inventories, manifest_bytes, b"{}"
    )
    # The existing source builder validates caller-pinned acquisition identities,
    # raw joins, boundary attribution and parent admission before projecting rows.
    replay = build_sead_source_native_evidence_bundle(
        raw, expected_identity=expected_identity
    )
    proofs = {}
    for name, expected in replay.items():
        observed = evidence.document(name)
        partitioned = observed.get("partitioned_fields", {})
        expected_metadata = {
            key: value for key, value in expected.items() if key not in partitioned
        }
        observed_metadata = {
            key: value for key, value in observed.items() if key != "partitioned_fields"
        }
        if canonical_bytes(expected_metadata) != canonical_bytes(observed_metadata):
            raise ValueError(
                f"SEAD raw projection differs from normalized metadata: {name}"
            )
        fields = {}
        for field in partitioned:
            expected_rows = expected[field]
            if not isinstance(expected_rows, list):
                raise ValueError("SEAD replay field must be a row list")
            digest = hashlib.sha256()
            count = 0
            for source in evidence.rows(name, field):
                if count >= len(
                    expected_rows
                ) or source.canonical_json != canonical_bytes(expected_rows[count]):
                    raise ValueError(
                        f"SEAD raw projection differs from normalized row: {name}:{field}:{count}"
                    )
                digest.update(source.canonical_json)
                count += 1
            if count != len(expected_rows):
                raise ValueError("SEAD replay row denominator differs")
            fields[field] = {
                "row_count": count,
                "canonical_json_lines_sha256": digest.hexdigest(),
            }
        proofs[name] = {
            "metadata_sha256": hashlib.sha256(
                canonical_bytes(expected_metadata)
            ).hexdigest(),
            "partitioned_fields": fields,
        }
    del replay
    receipt = {
        "status": "exact_source_replay_match",
        "producer": "build_sead_source_native_evidence_bundle",
        "acquisition_manifest_sha256": manifest["acquisition_manifest_sha256"],
        "normalized_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "documents": proofs,
    }
    evidence.assert_unchanged()
    return SeadEvidence(
        raw, normalized, boundary, inventories, manifest_bytes, canonical_bytes(receipt)
    )
