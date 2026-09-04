"""Build the governed cross-source country and dimension coverage ledger."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Final, cast

COUNTRIES: Final = ("SE", "DK", "NO", "FI", "UNASSIGNED", "OUTSIDE")
COUNTRY_DIMENSIONS: Final = (
    "source_reported",
    "governed_assignment",
    "publication",
)
SOURCE_FAMILIES: Final = (
    "landclim",
    "neotoma",
    "sead",
    "raa",
    "boundaries",
    "svar",
    "aadr",
    "animal_adna",
)
PRODUCER_VERSION: Final = "1"
LEDGER_SCHEMA_VERSION: Final = "country-dimension-coverage-ledger.v1"
CELL_SCHEMA_ID: Final = "https://bijux.io/schemas/pollenomics/country-coverage.v2.json"
BOUNDARY_METHOD: Final = "natural-earth-5.1.1-strict-containment-with-review.v1"
PUBLICATION_METHOD: Final = "product-country-publication-partition.v1"

COUNT_FIELDS: Final = (
    "requested_records",
    "received_records",
    "deduplicated_records",
    "failed_records",
    "accepted_records",
    "excluded_records",
    "unresolved_records",
    "published_records",
    "sites",
    "datasets",
    "collection_units",
    "samples",
    "dated_samples",
    "age_claims",
    "observations",
    "distinct_taxa",
    "mapped_taxa",
    "ambiguous_taxa",
    "unmapped_taxa",
    "events",
    "evaluated_pairs",
    "definite_candidates",
    "possible_candidates",
    "indeterminate_order_pairs",
    "unresolved_pairs",
    "excluded_pairs",
    "refused_pre_candidate_pairs",
)

INPUT_PATHS: Final = (
    "data/source_family_evidence_stage_matrix.json",
    "data/collection_summary.json",
    "data/boundaries/raw/source_manifest.json",
    "data/landclim/normalized/nordic_pollen_site_sequences.geojson",
    "data/neotoma/relational/reconciliation.json",
    "data/sead/raw/acquisitions/sead-live-d1fd2058913372eda1c12e526e0eb7c8a6cec415e9f9e9b5b92b8896597b35ac/admission.json",
    "data/sead/raw/acquisitions/sead-live-d1fd2058913372eda1c12e526e0eb7c8a6cec415e9f9e9b5b92b8896597b35ac/country-decisions.json",
    "docs/report/regions/nordic/nordic_pollen_site_sequences.geojson",
    "docs/report/regions/nordic/nordic_pollen_sites.geojson",
    "docs/report/countries/sweden/sweden_aadr_v66_summary.json",
    "docs/report/countries/denmark/denmark_aadr_v66_summary.json",
    "docs/report/countries/norway/norway_aadr_v66_summary.json",
    "docs/report/countries/finland/finland_aadr_v66_summary.json",
    "docs/report/animal_country_species_coverage.json",
)

_NAME_TO_CODE: Final = {
    "Sweden": "SE",
    "Denmark": "DK",
    "Norway": "NO",
    "Finland": "FI",
    "SE": "SE",
    "SWE": "SE",
    "SWE (Sweden)": "SE",
    "DK": "DK",
    "DK (Denmark)": "DK",
    "NO": "NO",
    "NOR": "NO",
    "NOR (Norway)": "NO",
    "FI": "FI",
    "FIN": "FI",
    "FIN (Finland)": "FI",
}


class CountryCoverageError(ValueError):
    """Raised when governed coverage evidence cannot be reconciled."""


def build_country_dimension_coverage_ledger(
    repository_root: Path, *, cell_schema_path: Path
) -> dict[str, object]:
    """Build and validate a deterministic ledger from current governed artifacts."""
    root = repository_root.resolve(strict=True)
    schema_path = cell_schema_path.resolve(strict=True)
    schema_bytes = schema_path.read_bytes()
    schema = _object(json.loads(schema_bytes), "country coverage schema")
    if schema.get("$id") != CELL_SCHEMA_ID:
        raise CountryCoverageError("country coverage schema identity is not v2")

    inputs = [
        {
            "path": path,
            "sha256": _sha256((root / path).read_bytes()),
            "byte_count": (root / path).stat().st_size,
        }
        for path in INPUT_PATHS
    ]
    producer_path = Path(__file__).resolve()
    producer = {
        "path": producer_path.relative_to(root).as_posix(),
        "version": PRODUCER_VERSION,
        "sha256": _sha256(producer_path.read_bytes()),
    }
    configuration = {
        "cell_schema_id": CELL_SCHEMA_ID,
        "countries": list(COUNTRIES),
        "country_dimensions": list(COUNTRY_DIMENSIONS),
        "source_families": list(SOURCE_FAMILIES),
        "count_fields": list(COUNT_FIELDS),
        "input_paths": list(INPUT_PATHS),
    }
    config_digest = f"sha256:{_sha256(_canonical_bytes(configuration))}"
    identity = {
        "cell_schema_sha256": _sha256(schema_bytes),
        "config_digest": config_digest,
        "inputs": inputs,
        "producer": producer,
    }
    build_id = f"sha256:{_sha256(_canonical_bytes(identity))}"

    stage_rows = {
        str(row["source_key"]): row
        for row in _rows(
            _load(root / "data/source_family_evidence_stage_matrix.json"),
            "source stage matrix",
        )
    }
    if tuple(stage_rows) != SOURCE_FAMILIES:
        raise CountryCoverageError("source stage matrix order or inventory changed")
    collection = _load(root / "data/collection_summary.json")
    boundary_manifest = _load(root / "data/boundaries/raw/source_manifest.json")
    boundary_digest = (
        f"sha256:{_required_text(boundary_manifest, 'normalized_artifact', 'sha256')}"
    )

    evidence = _coverage_evidence(root)
    snapshot_ids = _source_snapshot_ids(collection, root)
    cells: list[dict[str, object]] = []
    for source_family in SOURCE_FAMILIES:
        stage = stage_rows[source_family]
        for dimension in COUNTRY_DIMENSIONS:
            for country_code in COUNTRIES:
                cells.append(
                    _cell(
                        source_family=source_family,
                        dimension=dimension,
                        country_code=country_code,
                        evidence=evidence,
                        stage=stage,
                        snapshot_id=snapshot_ids[source_family],
                        boundary_digest=boundary_digest,
                        config_digest=config_digest,
                        build_id=build_id,
                    )
                )

    _validate_cells(cells, schema)
    _validate_reconciliation(cells)
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "cell_schema_id": CELL_SCHEMA_ID,
        "cell_schema_sha256": _sha256(schema_bytes),
        "producer": producer,
        "config_digest": config_digest,
        "build_id": build_id,
        "input_artifacts": inputs,
        "source_family_count": len(SOURCE_FAMILIES),
        "country_dimension_count": len(COUNTRY_DIMENSIONS),
        "country_partition_count": len(COUNTRIES),
        "cell_count": len(cells),
        "cells": cells,
    }


def write_country_dimension_coverage_ledger(
    repository_root: Path, *, cell_schema_path: Path, output_path: Path
) -> bytes:
    """Atomically write the ledger and return its canonical bytes."""
    payload = _canonical_bytes(
        build_country_dimension_coverage_ledger(
            repository_root, cell_schema_path=cell_schema_path
        )
    )
    root = repository_root.resolve(strict=True)
    destination = output_path.resolve()
    try:
        destination.relative_to(root)
    except ValueError as error:
        raise CountryCoverageError(
            "country coverage output must remain inside the repository"
        ) from error
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".writing", dir=destination.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), 0o644)
        os.replace(temporary_name, destination)
    finally:
        Path(temporary_name).unlink(missing_ok=True)
    return payload


def _coverage_evidence(
    root: Path,
) -> dict[tuple[str, str, str], dict[str, int | None]]:
    evidence: dict[tuple[str, str, str], dict[str, int | None]] = {}

    landclim = _load(root / INPUT_PATHS[3])
    reported = Counter[str]()
    for feature in _features(landclim, "LandClim normalized sites"):
        properties = _object(feature.get("properties"), "LandClim properties")
        popup = properties.get("popup_rows")
        if not isinstance(popup, list):
            raise CountryCoverageError("LandClim source country evidence is missing")
        value = next(
            (
                str(row.get("value"))
                for row in popup
                if isinstance(row, Mapping) and row.get("label") == "Reported country"
            ),
            None,
        )
        code = _country_code(value)
        reported[code] += 1
    _site_partition(evidence, "landclim", "source_reported", reported)
    _site_partition(
        evidence,
        "landclim",
        "publication",
        _geojson_country_counts(_load(root / INPUT_PATHS[7])),
        published=True,
    )

    neotoma = _object(
        _load(root / "data/neotoma/relational/reconciliation.json").get(
            "reconciliation"
        ),
        "Neotoma reconciliation",
    )
    attribution = _object(
        neotoma.get("country_attribution_counts"), "country attribution"
    )
    _site_partition(
        evidence,
        "neotoma",
        "source_reported",
        _integer_counts(attribution.get("raw_country_codes"), "Neotoma raw countries"),
    )
    country_rows = _object(neotoma.get("country_counts"), "Neotoma country counts")
    for country, raw_counts in country_rows.items():
        counts = _object(raw_counts, f"Neotoma {country} counts")
        evidence[("neotoma", "governed_assignment", country)] = {
            **_empty_counts(),
            "accepted_records": _integer(
                counts.get("assigned_sites"), "Neotoma assigned sites"
            ),
            "excluded_records": _integer(
                counts.get("refused_sites"), "Neotoma refused sites"
            ),
            "unresolved_records": _integer(
                counts.get("review_sites"), "Neotoma review sites"
            ),
            "sites": _integer(counts.get("sites"), "Neotoma sites"),
            "datasets": _integer(counts.get("datasets"), "Neotoma datasets"),
            "collection_units": _integer(
                counts.get("collection_units"), "Neotoma collection units"
            ),
            "samples": _integer(counts.get("samples"), "Neotoma samples"),
            "age_claims": _integer(counts.get("age_claim_rows"), "Neotoma age claims"),
            "observations": _integer(
                counts.get("observation_rows"), "Neotoma observations"
            ),
        }
    evidence[("neotoma", "governed_assignment", "OUTSIDE")] = {
        **_empty_counts(),
        "accepted_records": 0,
        "excluded_records": 0,
        "unresolved_records": 0,
        "sites": 0,
    }
    _site_partition(
        evidence,
        "neotoma",
        "publication",
        _geojson_country_counts(_load(root / INPUT_PATHS[8])),
        published=True,
    )

    decisions = _rows(
        _load(root / INPUT_PATHS[6]), "SEAD country decisions", key="decisions"
    )
    _site_partition(
        evidence,
        "sead",
        "source_reported",
        Counter({"UNASSIGNED": len(decisions)}),
    )
    governed = Counter[str]()
    for record in decisions:
        decision = _object(record.get("decision"), "SEAD country decision")
        if decision.get("decision_status") == "assigned":
            governed[_required_text(record, "governed_country_code")] += 1
        elif decision.get("refusal_reason") == "outside_governed_boundaries":
            governed["OUTSIDE"] += 1
        else:
            governed["UNASSIGNED"] += 1
    _site_partition(evidence, "sead", "governed_assignment", governed)
    for country in ("SE", "DK", "NO", "FI"):
        counts = evidence[("sead", "governed_assignment", country)]
        counts["accepted_records"] = counts["sites"]
        counts["unresolved_records"] = 0
        counts["excluded_records"] = 0
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["accepted_records"] = 0
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["unresolved_records"] = (
        governed["UNASSIGNED"]
    )
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["excluded_records"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["accepted_records"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["unresolved_records"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["excluded_records"] = governed[
        "OUTSIDE"
    ]

    boundary_countries = _object(
        _load(root / "data/boundaries/raw/source_manifest.json"),
        "boundary manifest",
    )
    artifacts = _object(
        boundary_countries.get("country_artifacts"), "boundary countries"
    )
    boundary_counts = Counter(
        {
            _country_code(name): _integer(
                _object(value, "boundary artifact").get("feature_count"),
                "boundary feature count",
            )
            for name, value in artifacts.items()
        }
    )
    _record_partition(evidence, "boundaries", "source_reported", boundary_counts)
    _record_partition(evidence, "boundaries", "governed_assignment", boundary_counts)
    _record_partition(
        evidence, "boundaries", "publication", boundary_counts, published=True
    )

    for country, path in (
        ("SE", INPUT_PATHS[9]),
        ("DK", INPUT_PATHS[10]),
        ("NO", INPUT_PATHS[11]),
        ("FI", INPUT_PATHS[12]),
    ):
        summary = _load(root / path)
        evidence[("aadr", "publication", country)] = {
            **_empty_counts(),
            "published_records": _integer(
                summary.get("total_unique_samples"), "AADR samples"
            ),
            "sites": _integer(
                summary.get("total_unique_localities"), "AADR localities"
            ),
            "samples": _integer(summary.get("total_unique_samples"), "AADR samples"),
        }

    animal_rows = _rows(_load(root / INPUT_PATHS[13]), "animal coverage")
    animal_counts: Counter[str] = Counter()
    animal_sites: Counter[str] = Counter()
    for row in animal_rows:
        country = _country_code(str(row.get("country")))
        animal_counts[country] += _integer(
            row.get("mapped_sample_count"), "animal mapped samples"
        )
        animal_sites[country] += _integer(
            row.get("direct_coordinate_site_count"), "animal sites"
        )
    for country in ("SE", "DK", "NO", "FI"):
        evidence[("animal_adna", "publication", country)] = {
            **_empty_counts(),
            "published_records": animal_counts[country],
            "samples": animal_counts[country],
            "sites": animal_sites[country],
        }
    return evidence


def _cell(
    *,
    source_family: str,
    dimension: str,
    country_code: str,
    evidence: Mapping[tuple[str, str, str], dict[str, int | None]],
    stage: Mapping[str, object],
    snapshot_id: str,
    boundary_digest: str,
    config_digest: str,
    build_id: str,
) -> dict[str, object]:
    key = (source_family, dimension, country_code)
    counts = evidence.get(key)
    reasons: list[str] = []
    assignment_method = (
        None
        if dimension == "source_reported"
        else BOUNDARY_METHOD
        if dimension == "governed_assignment"
        else PUBLICATION_METHOD
    )
    authority = str(stage.get("authority_status"))
    blocking = _text_list(stage.get("blocking_reasons"), "blocking reasons")
    authority_reasons = _text_list(stage.get("authority_reasons"), "authority reasons")
    if counts is None:
        counts = _empty_counts()
        availability = "blocked"
        lifecycle = "unavailable"
        reasons.append(f"{dimension}_partition_not_materialized")
    else:
        availability = (
            "zero_observations"
            if not any(value for value in counts.values() if value is not None)
            else "available_collected"
        )
        lifecycle = "admitted"
    if source_family in {"raa", "svar"}:
        counts = _empty_counts()
        if country_code == "SE":
            availability = "blocked"
            lifecycle = "refused"
            reasons.extend(authority_reasons)
        else:
            availability = "not_available_from_source"
            lifecycle = "unavailable"
            reasons.append("national_source_sweden_only")
    elif source_family == "boundaries":
        lifecycle = "review_required"
        reasons.extend(authority_reasons)
    elif source_family == "sead" and dimension == "governed_assignment":
        if country_code == "UNASSIGNED":
            lifecycle = "review_required"
            availability = "unresolved"
            reasons.append("boundary_assignment_review_required")
        elif country_code == "OUTSIDE":
            lifecycle = "refused"
            availability = "available_partial"
            reasons.append("outside_governed_boundaries")
    elif source_family == "sead" and dimension == "publication":
        lifecycle = "unavailable"
        availability = "blocked"
        reasons.append("missing_published_surface")
    elif source_family == "aadr":
        lifecycle = "review_required"
        reasons.extend(blocking)
    if (
        dimension == "source_reported"
        and country_code == "UNASSIGNED"
        and any(value for value in counts.values() if value is not None)
    ):
        availability = "available_partial"
        reasons.append("source_country_not_reported")
    if (
        dimension == "governed_assignment"
        and country_code == "UNASSIGNED"
        and any(value for value in counts.values() if value is not None)
    ):
        availability = "unresolved"
        lifecycle = "review_required"
        reasons.append("country_assignment_review_required")
    if country_code in {"UNASSIGNED", "OUTSIDE"} and not reasons:
        if any(value for value in counts.values() if value is not None):
            reasons.append("explicit_non_nordic_partition")
        else:
            reasons.append("explicit_empty_partition")
    if authority == "refused" and lifecycle not in {"refused", "unavailable"}:
        lifecycle = "refused"
        reasons.extend(authority_reasons)
    return {
        "schema_version": "2.0.0",
        "country_code": country_code,
        "country_dimension": dimension,
        "country_assignment_method": assignment_method,
        "source_family": source_family,
        "resolution": "source",
        "feature_key": None,
        "classification_contract_version": None,
        "availability_status": availability,
        "lifecycle_status": lifecycle,
        "counts": counts,
        "reason_codes": sorted(set(reasons)),
        "source_snapshot_id": snapshot_id,
        "boundary_artifact_digest": (
            None if dimension == "source_reported" else boundary_digest
        ),
        "config_digest": config_digest,
        "producer_version": PRODUCER_VERSION,
        "build_id": build_id,
    }


def _source_snapshot_ids(
    collection: Mapping[str, object], root: Path
) -> dict[str, str]:
    source_hashes = _object(collection.get("source_hashes"), "source hashes")
    result = {
        source: f"sha256:{_required_text(_object(source_hashes[source], source), 'snapshot_sha256')}"
        for source in (
            "landclim",
            "neotoma",
            "sead",
            "raa",
            "boundaries",
            "svar",
            "aadr",
        )
    }
    result["neotoma"] = _required_text(
        _load(root / "data/neotoma/relational/reconciliation.json"),
        "source_snapshot_id",
    )
    result["sead"] = _required_text(
        _load(root / INPUT_PATHS[5]), "acquisition_bundle_sha256"
    )
    result["animal_adna"] = f"sha256:{_sha256((root / INPUT_PATHS[13]).read_bytes())}"
    return result


def _site_partition(
    evidence: dict[tuple[str, str, str], dict[str, int | None]],
    source: str,
    dimension: str,
    values: Mapping[str, int],
    *,
    published: bool = False,
) -> None:
    for country in COUNTRIES:
        value = int(values.get(country, 0))
        evidence[(source, dimension, country)] = {
            **_empty_counts(),
            "received_records": value if dimension == "source_reported" else None,
            "published_records": value if published else None,
            "sites": value,
        }


def _record_partition(
    evidence: dict[tuple[str, str, str], dict[str, int | None]],
    source: str,
    dimension: str,
    values: Mapping[str, int],
    *,
    published: bool = False,
) -> None:
    for country in COUNTRIES:
        value = int(values.get(country, 0))
        evidence[(source, dimension, country)] = {
            **_empty_counts(),
            "received_records": value if dimension == "source_reported" else None,
            "accepted_records": value if dimension == "governed_assignment" else None,
            "published_records": value if published else None,
        }


def _empty_counts() -> dict[str, int | None]:
    return dict.fromkeys(COUNT_FIELDS)


def _validate_cells(
    cells: list[dict[str, object]], schema: Mapping[str, object]
) -> None:
    try:
        from jsonschema import Draft202012Validator  # type: ignore[import-untyped]
    except ImportError as error:
        raise CountryCoverageError("jsonschema is required") from error
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for index, cell in enumerate(cells):
        errors = sorted(validator.iter_errors(cell), key=lambda item: list(item.path))
        if errors:
            raise CountryCoverageError(
                f"cell {index} violates schema: {errors[0].message}"
            )


def _validate_reconciliation(cells: list[dict[str, object]]) -> None:
    expected_keys = {
        (source, dimension, country)
        for source in SOURCE_FAMILIES
        for dimension in COUNTRY_DIMENSIONS
        for country in COUNTRIES
    }
    observed_keys = {
        (
            str(cell["source_family"]),
            str(cell["country_dimension"]),
            str(cell["country_code"]),
        )
        for cell in cells
    }
    if observed_keys != expected_keys or len(cells) != len(expected_keys):
        raise CountryCoverageError("country coverage cell inventory does not reconcile")
    if any(cell["availability_status"] == "unknown" for cell in cells):
        raise CountryCoverageError("country coverage cannot retain unknown cells")
    for cell in cells:
        counts = _object(cell.get("counts"), "country coverage counts")
        if tuple(counts) != COUNT_FIELDS:
            raise CountryCoverageError("country coverage count inventory changed")

    index = {
        (
            str(cell["source_family"]),
            str(cell["country_dimension"]),
            str(cell["country_code"]),
        ): cell
        for cell in cells
    }

    def total(source: str, dimension: str, measure: str) -> int:
        result = 0
        for country in COUNTRIES:
            counts = _object(index[(source, dimension, country)]["counts"], "counts")
            value = counts.get(measure)
            if not isinstance(value, int) or isinstance(value, bool):
                raise CountryCoverageError(
                    f"{source} {dimension} {measure} has an incomplete denominator"
                )
            result += value
        return result

    landclim_reported = total("landclim", "source_reported", "sites")
    if landclim_reported != total("landclim", "publication", "sites"):
        raise CountryCoverageError("LandClim site partitions do not reconcile")
    neotoma_reported = total("neotoma", "source_reported", "sites")
    if neotoma_reported != total("neotoma", "governed_assignment", "sites"):
        raise CountryCoverageError("Neotoma governed sites do not reconcile")
    if neotoma_reported != total("neotoma", "publication", "sites"):
        raise CountryCoverageError("Neotoma publication sites do not reconcile")
    neotoma_accounted = sum(
        total("neotoma", "governed_assignment", measure)
        for measure in ("accepted_records", "unresolved_records", "excluded_records")
    )
    if neotoma_reported != neotoma_accounted:
        raise CountryCoverageError("Neotoma admission outcomes do not reconcile")
    sead_received = total("sead", "source_reported", "received_records")
    sead_governed_sites = total("sead", "governed_assignment", "sites")
    if sead_received != sead_governed_sites:
        raise CountryCoverageError("SEAD country decisions do not reconcile")
    sead_accounted = sum(
        total("sead", "governed_assignment", measure)
        for measure in ("accepted_records", "unresolved_records", "excluded_records")
    )
    if sead_received != sead_accounted:
        raise CountryCoverageError("SEAD admission outcomes do not reconcile")
    boundary_received = total("boundaries", "source_reported", "received_records")
    if boundary_received != total(
        "boundaries", "governed_assignment", "accepted_records"
    ):
        raise CountryCoverageError("boundary admission does not reconcile")
    if boundary_received != total("boundaries", "publication", "published_records"):
        raise CountryCoverageError("boundary publication does not reconcile")


def _geojson_country_counts(document: Mapping[str, object]) -> Counter[str]:
    return Counter(
        _country_code(
            str(_object(feature.get("properties"), "feature properties").get("country"))
        )
        for feature in _features(document, "country GeoJSON")
    )


def _features(document: Mapping[str, object], label: str) -> list[Mapping[str, object]]:
    features = document.get("features")
    if not isinstance(features, list) or any(
        not isinstance(feature, Mapping) for feature in features
    ):
        raise CountryCoverageError(f"{label} must contain feature objects")
    return cast(list[Mapping[str, object]], features)


def _integer_counts(value: object, label: str) -> dict[str, int]:
    mapping = _object(value, label)
    return {str(key): _integer(item, label) for key, item in mapping.items()}


def _country_code(value: str | None) -> str:
    if value is None:
        return "UNASSIGNED"
    try:
        return _NAME_TO_CODE[value]
    except KeyError as error:
        raise CountryCoverageError(f"unsupported country label: {value!r}") from error


def _rows(
    document: Mapping[str, object], label: str, *, key: str = "rows"
) -> list[Mapping[str, object]]:
    value = document.get(key)
    if not isinstance(value, list) or any(
        not isinstance(row, Mapping) for row in value
    ):
        raise CountryCoverageError(f"{label} must contain object rows")
    return cast(list[Mapping[str, object]], value)


def _load(path: Path) -> dict[str, Any]:
    try:
        return _object(json.loads(path.read_bytes()), path.as_posix())
    except (OSError, json.JSONDecodeError) as error:
        raise CountryCoverageError(f"cannot read governed input: {path}") from error


def _object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CountryCoverageError(f"{label} must be an object")
    return cast(dict[str, Any], value)


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CountryCoverageError(f"{label} must be a non-negative integer")
    return value


def _text_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item for item in value
    ):
        raise CountryCoverageError(f"{label} must be a list of non-empty strings")
    return cast(list[str], value)


def _required_text(document: Mapping[str, object], *path: str) -> str:
    value: object = document
    for key in path:
        if not isinstance(value, Mapping):
            raise CountryCoverageError(f"missing required field: {'.'.join(path)}")
        value = value.get(key)
    if not isinstance(value, str) or not value:
        raise CountryCoverageError(f"missing required field: {'.'.join(path)}")
    return value


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()
