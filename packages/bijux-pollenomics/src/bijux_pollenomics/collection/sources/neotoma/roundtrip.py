"""Reconcile native Neotoma hierarchy rows with governed relational evidence."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
import hashlib
import json
from pathlib import Path

from bijux_pollenomics.evidence.sources.neotoma import (
    validate_neotoma_relational_materialization,
)

from .production import load_validated_neotoma_raw_archive
from .relational.identifiers import optional_source_id

SURFACES = (
    "sites",
    "collection_units",
    "datasets",
    "chronologies",
    "chronology_controls",
    "samples",
    "age_claims",
    "observations",
)
REPEATED_ROWS = frozenset({"age_claims", "observations"})


def _digest(value: object) -> str:
    content = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def _record(surface: str, parents: tuple[str, ...], payload: object) -> str:
    return _digest([surface, parents, payload])


def _object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"Expected object: {label}")
    return value


def _array(value: object, label: str) -> list[object]:
    if not isinstance(value, list):
        raise ValueError(f"Expected array: {label}")
    return value


def _id(prefix: str, value: object) -> str:
    if value is None or isinstance(value, bool) or not str(value).strip():
        raise ValueError(f"Missing native {prefix} identifier")
    return f"neotoma:{prefix}:{value}"


def native_hierarchy(rows: Iterable[Mapping[str, object]]) -> dict[str, Counter[str]]:
    """Count source payloads in their native parent scope, including repeats."""
    found: dict[str, Counter[str]] = {surface: Counter() for surface in SURFACES}
    for download in rows:
        site = _object(download.get("site"), "site")
        site_id = _id("site", site.get("siteid"))
        found["sites"][
            _record(
                "sites",
                (site_id,),
                {
                    key: value
                    for key, value in site.items()
                    if key not in {"collectionunit", "dataset"}
                },
            )
        ] += 1
        unit = _object(site.get("collectionunit"), "collection unit")
        unit_id = _id("collection-unit", unit.get("collectionunitid"))
        found["collection_units"][
            _record(
                "collection_units",
                (site_id, unit_id),
                {
                    key: value
                    for key, value in unit.items()
                    if key not in {"dataset", "chronologies", "defaultchronology"}
                },
            )
        ] += 1
        dataset = _object(unit.get("dataset"), "dataset")
        dataset_id = _id("dataset", dataset.get("datasetid"))
        parents = (site_id, unit_id, dataset_id)
        found["datasets"][
            _record(
                "datasets",
                parents,
                {key: value for key, value in dataset.items() if key != "samples"},
            )
        ] += 1
        for wrapper_value in _array(unit.get("chronologies"), "chronologies"):
            wrapper = _object(wrapper_value, "chronology wrapper")
            chronology = _object(wrapper.get("chronology"), "chronology")
            chronology_source_id = optional_source_id(chronology.get("chronologyid"))
            chronology_key = chronology_source_id or (
                f"unidentified:{_digest(dict(chronology))[:20]}"
            )
            chronology_id = (
                f"neotoma:chronology:{unit['collectionunitid']}:{chronology_key}"
            )
            found["chronologies"][
                _record(
                    "chronologies",
                    (site_id, unit_id, chronology_id),
                    {
                        key: value
                        for key, value in chronology.items()
                        if key != "chroncontrols"
                    },
                )
            ] += 1
            for control in _array(chronology.get("chroncontrols"), "controls"):
                found["chronology_controls"][
                    _record(
                        "chronology_controls",
                        (site_id, unit_id, chronology_id),
                        control,
                    )
                ] += 1
        for sample_value in _array(dataset.get("samples"), "samples"):
            sample = _object(sample_value, "sample")
            sample_id = _id("sample", sample.get("sampleid"))
            sample_parents = (*parents, sample_id)
            found["samples"][
                _record(
                    "samples",
                    sample_parents,
                    {
                        key: value
                        for key, value in sample.items()
                        if key not in {"ages", "datum"}
                    },
                )
            ] += 1
            for age in _array(sample.get("ages"), "ages"):
                found["age_claims"][_record("age_claims", sample_parents, age)] += 1
            for datum in _array(sample.get("datum"), "datum"):
                found["observations"][
                    _record("observations", sample_parents, datum)
                ] += 1
    return found


def _surface_record(surface: str, row: Mapping[str, object]) -> str:
    parents = tuple(
        str(row[field])
        for field in ("site_id", "collection_unit_id", "dataset_id", "sample_id")
        if field in row
    )
    if surface == "sites":
        parents = (str(row["site_id"]),)
    elif surface in {"chronologies", "chronology_controls"}:
        parents = (
            str(row["site_id"]),
            str(row["collection_unit_id"]),
            str(row["chronology_id"]),
        )
    elif surface == "collection_units":
        parents = (str(row["site_id"]), str(row["collection_unit_id"]))
    elif surface == "age_claims":
        parents = (
            str(row["site_id"]),
            str(row["collection_unit_id"]),
            str(row["dataset_id"]),
            str(row["subject_id"]),
        )
    return _record(surface, parents, row["source_payload"])


def reconcile_hierarchy(
    native: Mapping[str, Counter[str]],
    surfaces: Mapping[str, Iterable[Mapping[str, object]]],
    conflicts: Iterable[Mapping[str, object]],
) -> dict[str, object]:
    """Match source values to accepted rows or retained conflict variants."""
    conflict_rows: dict[str, list[Mapping[str, object]]] = {
        name: [] for name in SURFACES
    }
    for conflict in conflicts:
        kind = conflict.get("conflict_kind")
        surface = (
            "chronology_controls"
            if kind == "chronology_control_payload_conflict"
            else None
        )
        if surface is None:
            continue
        detail = _object(conflict.get("detail"), "conflict detail")
        for variant in _array(detail.get("variants"), "conflict variants"):
            conflict_rows[surface].append(_object(variant, "conflict variant"))
    comparisons: dict[str, object] = {}
    all_match = True
    for surface in SURFACES:
        accepted = Counter(_surface_record(surface, row) for row in surfaces[surface])
        retained = accepted | Counter(
            _surface_record(surface, row) for row in conflict_rows[surface]
        )
        expected = native[surface]
        if surface in REPEATED_ROWS:
            missing_count = (expected - retained).total()
            unexpected_count = (retained - expected).total()
        else:
            missing_count = len(expected.keys() - retained.keys())
            unexpected_count = len(retained.keys() - expected.keys())
        match = missing_count == 0 and unexpected_count == 0
        all_match &= match
        comparisons[surface] = {
            "raw_rows": expected.total(),
            "raw_distinct_parent_payloads": len(expected),
            "accepted_rows": accepted.total(),
            "conflict_variant_rows": len(conflict_rows[surface]),
            "missing_rows": missing_count,
            "unexpected_rows": unexpected_count,
            "match": match,
        }
    return {"match": all_match, "surfaces": comparisons}


def audit_neotoma_roundtrip(raw_root: Path, relational_root: Path) -> dict[str, object]:
    """Validate both archives and compare every nested native source payload."""
    rows, source_id = load_validated_neotoma_raw_archive(raw_root)
    manifest = validate_neotoma_relational_materialization(relational_root.resolve())
    if manifest["source_snapshot_id"] != source_id:
        raise ValueError("Raw and relational Neotoma source identities differ")
    surface_manifest = _object(manifest["surfaces"], "surfaces")
    surfaces: dict[str, list[Mapping[str, object]]] = {}
    for surface in (*SURFACES, "conflicts"):
        surface_rows: list[Mapping[str, object]] = []
        spec = _object(surface_manifest[surface], surface)
        for part_value in _array(spec["parts"], f"{surface} parts"):
            part = _object(part_value, "part")
            payload = json.loads((relational_root / str(part["path"])).read_text())
            surface_rows.extend(_object(row, surface) for row in payload["rows"])
        surfaces[surface] = surface_rows
    result = reconcile_hierarchy(
        native_hierarchy(rows), surfaces, surfaces["conflicts"]
    )
    return {
        "schema_version": "neotoma-native-roundtrip.v1",
        "source_snapshot_id": source_id,
        "materialization_sha256": manifest["materialization_sha256"],
        "raw_part_count": 9,
        "download_count": len(rows),
        "status": "complete" if result["match"] else "refused",
        "reconciliation": result,
    }
