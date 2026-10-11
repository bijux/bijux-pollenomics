"""Reconcile Neotoma variable attributes with native download datum keys."""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Iterable, Mapping
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.collection.sources.neotoma.production import (
    load_validated_neotoma_raw_archive,
)
from bijux_pollenomics.collection.sources.neotoma.relational.identifiers import digest
from bijux_pollenomics.collection.sources.neotoma.relational.variables import (
    variable_id,
)
from bijux_pollenomics.core.text import clean_optional_text
from bijux_pollenomics.evidence.sources.neotoma import (
    validate_neotoma_relational_materialization,
)


def _rows(value: object, label: str) -> list[Mapping[str, object]]:
    if not isinstance(value, list) or any(
        not isinstance(row, Mapping) for row in value
    ):
        raise ValueError(f"Neotoma {label} must contain object rows")
    return value


def _child(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Neotoma {label} must be an object")
    return value


def native_datums(
    downloads: Iterable[Mapping[str, object]],
) -> Iterable[Mapping[str, object]]:
    """Walk every native datum without dropping unknown taxon or group labels."""
    for download in downloads:
        site = _child(download.get("site"), "site")
        unit = _child(site.get("collectionunit"), "collection unit")
        dataset = _child(unit.get("dataset"), "dataset")
        for sample in _rows(dataset.get("samples"), "samples"):
            yield from _rows(sample.get("datum"), "datum")


def _semantics(datum: Mapping[str, object]) -> dict[str, object]:
    return {
        "source_taxon_group": datum.get("taxongroup"),
        "source_ecological_group": datum.get("ecologicalgroup"),
        "source_element": datum.get("element"),
        "source_element_type": datum.get("elementtype"),
    }


def _unit(datum: Mapping[str, object]) -> str | None:
    return clean_optional_text(datum.get("units")) or None


def reconcile(
    datums: Iterable[Mapping[str, object]],
    variables: Iterable[Mapping[str, object]],
    conflicts: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Check each variable against all native key, name, semantic and unit variants."""
    native: dict[str, dict[str, Any]] = {}
    datum_count = 0
    group_datum_counts: Counter[str] = Counter()
    for datum in datums:
        datum_count += 1
        key = variable_id(datum)
        group = datum.get("taxongroup")
        group_datum_counts[str(group) if group is not None else "<null>"] += 1
        record = native.setdefault(
            key,
            {
                "source_taxon_id": datum.get("taxonid"),
                "source_reported_name": datum.get("variablename"),
                "identities": {},
                "names": {},
                "semantics": {},
                "units": set(),
                "datum_count": 0,
            },
        )
        record["datum_count"] += 1
        identity = {"taxon_id": datum.get("taxonid"), "name": datum.get("variablename")}
        record["identities"][digest(identity)] = identity
        record["names"][digest(datum.get("variablename"))] = datum.get("variablename")
        semantics = _semantics(datum)
        record["semantics"][digest(semantics)] = semantics
        unit = _unit(datum)
        if unit is not None:
            record["units"].add(unit)

    relational: dict[str, Mapping[str, object]] = {}
    duplicate_ids: list[str] = []
    for variable in variables:
        candidate_key = variable.get("variable_id")
        if not isinstance(candidate_key, str):
            raise ValueError("Neotoma variable lacks variable_id")
        if candidate_key in relational:
            duplicate_ids.append(candidate_key)
        relational[candidate_key] = variable

    ledger = [
        conflict
        for conflict in conflicts
        if conflict.get("conflict_kind") == "variable_identity_conflict"
    ]
    ledger_by_subject: dict[str, set[str]] = {}
    for conflict in ledger:
        detail = _child(conflict.get("detail"), "variable conflict detail")
        subject = conflict.get("subject_id")
        if isinstance(subject, str):
            ledger_by_subject.setdefault(subject, set()).add(
                digest(
                    {
                        "existing_taxon_id": detail.get("existing_taxon_id"),
                        "incoming_taxon_id": detail.get("incoming_taxon_id"),
                        "existing_name": detail.get("existing_name"),
                        "incoming_name": detail.get("incoming_name"),
                    }
                )
            )

    mismatches: list[dict[str, object]] = []
    missing_conflict_rows: list[dict[str, object]] = []
    unexpected_conflict_rows: list[str] = []
    group_variable_counts: Counter[str] = Counter()
    for key, expected in native.items():
        raw_semantics = expected["semantics"]
        for semantics in raw_semantics.values():
            group = semantics["source_taxon_group"]
            group_variable_counts[str(group) if group is not None else "<null>"] += 1
        actual = relational.get(key)
        if actual is None:
            continue
        reasons: list[str] = []
        if actual.get("source_taxon_id") != expected["source_taxon_id"]:
            reasons.append("source_taxon_id")
        if actual.get("source_reported_name") != expected["source_reported_name"]:
            reasons.append("source_reported_name")
        actual_semantics = actual.get("source_semantics")
        if (
            not isinstance(actual_semantics, list)
            or {digest(value) for value in actual_semantics} != set(raw_semantics)
            or len(actual_semantics) != len(raw_semantics)
        ):
            reasons.append("source_semantics")
        if actual.get("source_units") != sorted(expected["units"]):
            reasons.append("source_units")
        if reasons:
            mismatches.append({"variable_id": key, "fields": reasons})
        expected_signatures: set[str] = set()
        for identity in expected["identities"].values():
            if (
                identity["taxon_id"] == expected["source_taxon_id"]
                and identity["name"] == expected["source_reported_name"]
            ):
                continue
            signature = digest(
                {
                    "existing_taxon_id": expected["source_taxon_id"],
                    "incoming_taxon_id": identity["taxon_id"],
                    "existing_name": expected["source_reported_name"],
                    "incoming_name": identity["name"],
                }
            )
            expected_signatures.add(signature)
            if signature not in ledger_by_subject.get(key, set()):
                missing_conflict_rows.append(
                    {"variable_id": key, "incoming_identity": identity}
                )
        if ledger_by_subject.get(key, set()) - expected_signatures:
            unexpected_conflict_rows.append(key)

    native_ids = set(native)
    relational_ids = set(relational)
    name_variant_ids = sorted(
        key for key, record in native.items() if len(record["names"]) > 1
    )
    identity_variant_ids = sorted(
        key for key, record in native.items() if len(record["identities"]) > 1
    )
    unidentified_ids = sorted(
        key for key, record in native.items() if record["source_taxon_id"] is None
    )
    orphan_ledger_ids = sorted(set(ledger_by_subject) - native_ids)
    missing_ids = sorted(native_ids - relational_ids)
    unexpected_ids = sorted(relational_ids - native_ids)
    return {
        "match": not (
            duplicate_ids
            or missing_ids
            or unexpected_ids
            or mismatches
            or missing_conflict_rows
            or unexpected_conflict_rows
            or orphan_ledger_ids
        ),
        "native_datum_rows": datum_count,
        "native_variable_count": len(native),
        "relational_variable_count": len(relational),
        "native_semantic_variant_count": sum(
            len(record["semantics"]) for record in native.values()
        ),
        "unidentified_taxon_variable_ids": unidentified_ids,
        "name_variant_variable_ids": name_variant_ids,
        "identity_variant_variable_ids": identity_variant_ids,
        "source_taxon_group_datum_counts": dict(sorted(group_datum_counts.items())),
        "source_taxon_group_semantic_variant_counts": dict(
            sorted(group_variable_counts.items())
        ),
        "variable_identity_conflict_rows": len(ledger),
        "missing_variable_ids": missing_ids,
        "unexpected_variable_ids": unexpected_ids,
        "duplicate_variable_ids": sorted(set(duplicate_ids)),
        "attribute_mismatches": mismatches,
        "missing_identity_conflict_rows": missing_conflict_rows,
        "unexpected_identity_conflict_subjects": sorted(unexpected_conflict_rows),
        "orphan_identity_conflict_subjects": orphan_ledger_ids,
    }


def build(repository: Path) -> dict[str, object]:
    """Bind a full native variable reconciliation to validated source identities."""
    raw_root = repository / "data/neotoma/raw/neotoma_pollen_dataset_downloads"
    relational_root = repository / "data/neotoma/relational"
    downloads, source_id = load_validated_neotoma_raw_archive(raw_root)
    manifest = validate_neotoma_relational_materialization(relational_root.resolve())
    if manifest.get("source_snapshot_id") != source_id:
        raise ValueError("Native and relational Neotoma source identities differ")
    surface_manifest = _child(manifest.get("surfaces"), "surface manifest")
    surfaces: dict[str, list[Mapping[str, object]]] = {}
    for name in ("variables", "conflicts"):
        spec = _child(surface_manifest.get(name), f"{name} manifest")
        rows: list[Mapping[str, object]] = []
        for part in _rows(spec.get("parts"), f"{name} parts"):
            path = relational_root / str(part["path"])
            rows.extend(_rows(json.loads(path.read_bytes()).get("rows"), name))
        surfaces[name] = rows
    return {
        "schema_version": "neotoma-native-variable-surface.v1",
        "source_family": "neotoma",
        "source_snapshot_id": source_id,
        "raw_manifest_sha256": sha256(
            (raw_root / "manifest.json").read_bytes()
        ).hexdigest(),
        "relational_manifest_sha256": sha256(
            (relational_root / "manifest.json").read_bytes()
        ).hexdigest(),
        "materialization_sha256": manifest["materialization_sha256"],
        "build_id": manifest["build_id"],
        "reconciliation": reconcile(
            native_datums(downloads), surfaces["variables"], surfaces["conflicts"]
        ),
        "claims_not_made": [
            "taxonomic_approval",
            "pollen_denominator",
            "original_http_receipt",
            "lra_admission",
        ],
    }


def main() -> None:
    """Write the native Neotoma variable reconciliation under artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repository = args.repository.resolve()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Absent repository artifact output required")
    report = build(repository)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    reconciliation = report["reconciliation"]
    if (
        not isinstance(reconciliation, Mapping)
        or reconciliation.get("match") is not True
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
