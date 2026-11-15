"""Offline qualification of separately retained native DOI-frozen resource shapes."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from ...client import _validated_neotoma_rows, positive_native_id
from ..receipts import _object, _read, _safe_root
from .models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
    NeotomaResourceSpec,
    NeotomaRetainedSource,
)
from .protocol import plan_from_json, resource_key
from .replay import replay_neotoma_resource_capture


class _UnavailableFrozenResource(ValueError):
    """The authenticated API entity explicitly contains a successful empty set."""


@dataclass(frozen=True)
class NeotomaFrozenResource:
    """Native fields and arrays remain intact; no current-download projection."""

    parser_profile: str
    body_sha256: str
    payload: dict[str, Any]
    site: dict[str, Any]
    dataset: dict[str, Any]
    collection_unit: dict[str, Any]
    samples: list[dict[str, Any]]
    chronologies: list[dict[str, Any]]


def parse_neotoma_frozen_resource(
    resource: NeotomaResourceSpec, body: bytes, *, expected_body_sha256: str
) -> NeotomaFrozenResource:
    """Require exact native owners in either observed frozen wrapper shape."""
    if resource.exposure_role not in DEVELOPMENT_ROLES:
        raise ValueError("Frozen qualification refuses this exposure role")
    for value in (resource.dataset_id, resource.site_id, resource.collection_unit_id):
        positive_native_id(value)
    if sha256(body).hexdigest() != expected_body_sha256:
        raise ValueError("Frozen source body identity differs")
    payload = _object(body)
    rows = _validated_neotoma_rows(payload)
    if payload.get("status") != "success":
        raise ValueError("Frozen native source status is unsuccessful")
    if not rows:
        raise _UnavailableFrozenResource(
            "Frozen API explicitly returned successful empty data; absence is not certified"
        )
    if len(rows) != 1:
        raise ValueError("Frozen native response must contain exactly one download")
    download = rows[0].get("download")
    if not isinstance(download, dict):
        raise ValueError("Frozen native response download is malformed")
    data = download.get("data")
    if not isinstance(data, dict) or ("dataset" in data) == ("site" in data):
        raise ValueError("Frozen native metadata wrapper is unsupported or ambiguous")
    if "dataset" in data:
        wrapper = data["dataset"]
        if not isinstance(wrapper, dict):
            raise ValueError("Frozen dataset wrapper is malformed")
        site, dataset = wrapper.get("site"), wrapper.get("dataset")
        unit = site
        profile = "doi_frozen_dataset_wrapper.v1"
    else:
        site = data["site"]
        dataset = site.get("dataset") if isinstance(site, dict) else None
        unit = site.get("collectionunit") if isinstance(site, dict) else None
        profile = "doi_frozen_site_wrapper.v1"
    if (
        not isinstance(site, dict)
        or not isinstance(dataset, dict)
        or not isinstance(unit, dict)
    ):
        raise ValueError("Frozen native site, unit or dataset metadata is malformed")
    if (
        positive_native_id(site.get("siteid")) != resource.site_id
        or positive_native_id(unit.get("collectionunitid"))
        != resource.collection_unit_id
        or positive_native_id(dataset.get("datasetid")) != resource.dataset_id
        or dataset.get("datasettype") != resource.dataset_type
        or "database" not in dataset
        or dataset["database"] != resource.database
    ):
        raise ValueError("Frozen native dataset/site/unit/type/database owner differs")
    if (
        "collectionunitid" in site
        and positive_native_id(site["collectionunitid"]) != resource.collection_unit_id
    ):
        raise ValueError("Frozen native collection unit declarations disagree")
    nested_unit = site.get("collectionunit")
    if (
        isinstance(nested_unit, dict)
        and positive_native_id(nested_unit.get("collectionunitid"))
        != resource.collection_unit_id
    ):
        raise ValueError("Frozen native collection unit declarations disagree")
    for container in (site, unit):
        if "dataset" in container:
            declared = container["dataset"]
            if (
                not isinstance(declared, dict)
                or positive_native_id(declared.get("datasetid")) != resource.dataset_id
                or declared.get("datasettype") != resource.dataset_type
                or "database" not in declared
                or declared["database"] != resource.database
            ):
                raise ValueError("Frozen native dataset owner declarations disagree")
    samples = data.get("samples")
    chronology_wrapper = download.get("chronologies")
    chronologies = (
        chronology_wrapper.get("chronologies")
        if isinstance(chronology_wrapper, dict)
        else None
    )
    if not isinstance(samples, list) or not isinstance(chronologies, list):
        raise ValueError("Frozen native samples or chronologies must be arrays")
    for sample in samples:
        if (
            not isinstance(sample, dict)
            or not isinstance(sample.get("datum"), list)
            or any(not isinstance(datum, dict) for datum in sample["datum"])
        ):
            raise ValueError("Frozen native sample or datum row is malformed")
        for datum in sample["datum"]:
            if datum.get("units") is not None and not isinstance(datum["units"], str):
                raise ValueError("Frozen native source unit is malformed")
    if any(not isinstance(row, dict) for row in chronologies):
        raise ValueError("Frozen native chronology row is malformed")
    for row in chronologies:
        chronology = row.get("chronology")
        if "chronology" not in row or (
            chronology is not None and not isinstance(chronology, dict)
        ):
            raise ValueError("Frozen native chronology wrapper is malformed")
        if isinstance(chronology, dict) and (
            not isinstance(chronology.get("chroncontrols"), list)
            or any(
                not isinstance(control, dict) for control in chronology["chroncontrols"]
            )
        ):
            raise ValueError("Frozen native chronology control rows are malformed")
    return NeotomaFrozenResource(
        profile,
        expected_body_sha256,
        payload,
        site,
        dataset,
        unit,
        samples,
        chronologies,
    )


def _summary(parsed: NeotomaFrozenResource) -> dict[str, Any]:
    datums = [datum for sample in parsed.samples for datum in sample["datum"]]
    controls = []
    for row in parsed.chronologies:
        chronology = row.get("chronology")
        if isinstance(chronology, dict) and isinstance(
            chronology.get("chroncontrols"), list
        ):
            controls.extend(chronology["chroncontrols"])
    sample_ids = {
        sample["sampleid"]
        for sample in parsed.samples
        if type(sample.get("sampleid")) is int and sample["sampleid"] > 0
    }
    control_ids = {
        row["chroncontrolid"]
        for row in controls
        if isinstance(row, dict)
        and type(row.get("chroncontrolid")) is int
        and row["chroncontrolid"] > 0
    }
    units = {
        datum.get("units")
        for datum in datums
        if datum.get("units") is None or isinstance(datum.get("units"), str)
    }
    return {
        "parser_profile": parsed.parser_profile,
        "dataset_type": parsed.dataset["datasettype"],
        "database": parsed.dataset["database"],
        "sample_rows": len(parsed.samples),
        "distinct_identified_samples": len(sample_ids),
        "datum_rows": len(datums),
        "datum_rows_without_taxonid": sum("taxonid" not in datum for datum in datums),
        "datum_rows_null_taxonid": sum(
            "taxonid" in datum and datum["taxonid"] is None for datum in datums
        ),
        "source_units": sorted(
            units, key=lambda value: (value is not None, str(value))
        ),
        "chronology_rows": len(parsed.chronologies),
        "chroncontrol_rows": len(controls),
        "distinct_identified_chroncontrols": len(control_ids),
        "native_dataset_metadata": parsed.dataset,
        "native_site_metadata": parsed.site,
        "native_collection_unit_metadata": parsed.collection_unit,
        "native_samples_pointer": "/data/0/download/data/samples",
        "native_chronologies_pointer": "/data/0/download/chronologies/chronologies",
        "original_publication_identity": "not_asserted",
        "snapshot_date_interpretation": "No snapshot date inferred from retrieval time, chronology preparation, or current metadata",
        "units_interpreted": False,
        "scientific_admission": "not_asserted",
    }


def qualify_neotoma_frozen_capture(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    source_captures: Mapping[str, Path] | None = None,
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
) -> dict[str, Any]:
    """Derive a separate qualification ledger without relabelling captured results.

    Replay authenticates the original plan, all HTTP evidence and reuse closure.
    Each native body is decoded separately, retaining only summaries and original
    body locators. This function never requests source data or writes source files.
    """
    sources = source_captures or {}
    captured = replay_neotoma_resource_capture(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        source_captures=sources,
        retained_sources=retained_sources,
        limits=limits,
    )
    root = _safe_root(directory)
    manifest = _pinned_object(
        root / "capture-manifest.json", captured.manifest_sha256, 16 * 1024 * 1024
    )
    control = _pinned_object(
        root / "request-plan.json", manifest["plan_sha256"], 4 * 1024 * 1024
    )
    plan, _ = plan_from_json(control)
    specifications = {row.dataset_id: row for row in plan.resources}
    qualifications = []
    for entry in captured.resources:
        if entry["version"] != "doi_frozen":
            continue
        resource = specifications[entry["dataset_id"]]
        row: dict[str, Any] = {
            "resource_key": resource_key(resource, "doi_frozen"),
            "dataset_id": resource.dataset_id,
            "source_terminal_status": entry["terminal_status"],
            "scientific_admission": "not_asserted",
        }
        if resource.exposure_role not in DEVELOPMENT_ROLES:
            row["qualification_status"] = "not_qualified_exposure_role"
        elif entry["terminal_status"] != "unresolved_frozen_schema":
            row["qualification_status"] = "not_qualified_source_result"
        else:
            source_root, source_digest, source_entry = (
                root,
                captured.manifest_sha256,
                entry,
            )
            while "reused_from" in source_entry:
                source_digest = source_entry["reused_from"]["manifest_sha256"]
                source_root = _safe_root(sources[source_digest])
                previous = _pinned_object(
                    source_root / "capture-manifest.json",
                    source_digest,
                    16 * 1024 * 1024,
                )
                source_entry = next(
                    item
                    for item in previous["resources"]
                    if item["resource_key"] == row["resource_key"]
                )
            reference = source_entry["attempts"][-1]
            receipt = _pinned_object(
                source_root / reference["receipt_file"],
                reference["receipt_sha256"],
                65536,
            )
            body = _read(
                source_root / reference["body_file"], limits.max_response_bytes
            )
            if sha256(body).hexdigest() != receipt["retained_body_sha256"]:
                raise ValueError("Frozen qualification body identity differs")
            row["source"] = {
                "capture_manifest_sha256": source_digest,
                "resource_key": row["resource_key"],
                "receipt_file": reference["receipt_file"],
                "receipt_sha256": reference["receipt_sha256"],
                "body_file": reference["body_file"],
                "body_sha256": receipt["retained_body_sha256"],
                "utc_start": receipt["utc_start"],
                "utc_end": receipt["utc_end"],
                "requested_url": receipt["requested_url"],
                "tls_mode": receipt["tls_mode"],
            }
            try:
                parsed = parse_neotoma_frozen_resource(
                    resource, body, expected_body_sha256=receipt["retained_body_sha256"]
                )
                row.update(
                    qualification_status="parsed_frozen_native",
                    summary=_summary(parsed),
                )
                del parsed
            except _UnavailableFrozenResource as error:
                row.update(
                    qualification_status="unavailable_frozen_api_empty",
                    reason=str(error),
                    absence_certified=False,
                )
            except ValueError as error:
                row.update(
                    qualification_status="refused_frozen_native", reason=str(error)
                )
            del body
        qualifications.append(row)
    return {
        "schema_version": "neotoma-frozen-resource-qualification.v1",
        "source_capture_manifest_sha256": captured.manifest_sha256,
        "source_capture_relabelled": False,
        "resources": qualifications,
        "scientific_admission": "not_asserted",
    }


def _pinned_object(path: Path, digest: str, bound: int) -> dict[str, Any]:
    content = _read(path, bound)
    if sha256(content).hexdigest() != digest:
        raise ValueError("Frozen qualification source identity differs")
    return _object(content)
