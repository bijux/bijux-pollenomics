"""Cross-source country and dimension evidence derivation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from bijux_pollenomics.core.geospatial.geojson import CountryBoundaryCollection
from bijux_pollenomics.evidence.sources.sead import (
    SEAD_GOVERNED_EVIDENCE_RUN_ID,
    SEAD_GOVERNED_EVIDENCE_SCOPE_ID,
)
from .boundaries import (
    _boundary_component_index,
    _recomputed_country_decision,
    _validate_admission_copied_file,
)
from .constants import (
    BOUNDARY_METHOD,
    COUNTRIES,
    COUNT_FIELDS,
    CountryCoverageError,
    INPUT_PATHS,
    PRODUCER_VERSION,
    PUBLICATION_METHOD,
    SEAD_ADMISSION_PATH,
    SEAD_DECISIONS_PATH,
    SEAD_PUBLIC_SITES_PATH,
    SEAD_SITES_PATH,
    _AUTHORITY_STATUS_VALUES,
    _CODE_TO_NAME,
    _NORDIC_COUNTRY_CODES,
    _STAGE_STATUS_VALUES,
    _UUID_PATTERN,
)
from .decoding import (
    _bbox,
    _coordinate,
    _country_code,
    _features,
    _geojson_country_counts,
    _integer,
    _integer_counts,
    _object,
    _positive_integer,
    _require_sha256_id,
    _required_text,
    _rows,
    _sead_canonical_bytes,
    _sha256,
    _sha256_id_from_raw,
    _text_list,
)


def _validate_stage_rows(rows: list[Mapping[str, object]]) -> None:
    for row in rows:
        source = _required_text(row, "source_key")
        for field in (
            "raw_status",
            "normalized_status",
            "reviewed_status",
            "published_status",
        ):
            if row.get(field) not in _STAGE_STATUS_VALUES:
                raise CountryCoverageError(
                    f"{source} source stage has unsupported {field}"
                )
        if row.get("authority_status") not in _AUTHORITY_STATUS_VALUES:
            raise CountryCoverageError(
                f"{source} source stage has unsupported authority_status"
            )
        _text_list(row.get("blocking_reasons"), f"{source} blocking reasons")
        _text_list(row.get("authority_reasons"), f"{source} authority reasons")


def _coverage_evidence(
    documents: Mapping[str, Mapping[str, object]],
    *,
    input_bytes: Mapping[str, bytes],
    boundary_digest: str,
    boundary_version: str,
    boundary_collections: CountryBoundaryCollection,
    boundary_counts: Mapping[str, int],
    sead_claim_document: Mapping[str, object],
) -> dict[tuple[str, str, str], dict[str, int | None]]:
    evidence: dict[tuple[str, str, str], dict[str, int | None]] = {}

    landclim = documents[INPUT_PATHS[3]]
    reported = Counter[str]()
    for feature in _features(landclim, "LandClim normalized sites"):
        properties = _object(feature.get("properties"), "LandClim properties")
        popup = properties.get("popup_rows")
        if not isinstance(popup, list):
            raise CountryCoverageError("LandClim source country evidence is missing")
        reported_values = [
            row.get("value")
            for row in popup
            if isinstance(row, Mapping) and row.get("label") == "Reported country"
        ]
        if len(reported_values) > 1:
            raise CountryCoverageError(
                "LandClim feature contains duplicate Reported country labels"
            )
        value = reported_values[0] if reported_values else None
        code = _country_code(value)
        reported[code] += 1
    _site_partition(evidence, "landclim", "source_reported", reported)
    _site_partition(
        evidence,
        "landclim",
        "publication",
        _geojson_country_counts(documents[INPUT_PATHS[8]]),
        published=True,
    )

    neotoma = _object(
        documents["data/neotoma/relational/reconciliation.json"].get("reconciliation"),
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
    normalized_country_rows: dict[str, object] = {}
    for country, raw_counts in country_rows.items():
        country_code = _country_code(country)
        if country_code in normalized_country_rows:
            raise CountryCoverageError(
                "Neotoma governed countries contain a duplicate partition"
            )
        normalized_country_rows[country_code] = raw_counts
    for country, raw_counts in normalized_country_rows.items():
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
    if "OUTSIDE" not in normalized_country_rows:
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
        _geojson_country_counts(documents[INPUT_PATHS[9]]),
        published=True,
    )

    admission_document = documents[SEAD_ADMISSION_PATH]
    decision_document = documents[SEAD_DECISIONS_PATH]
    site_document = documents[SEAD_SITES_PATH]
    if site_document.get("schema_version") != "sead-table-payload.v1":
        raise CountryCoverageError("SEAD site payload schema is inconsistent")
    if site_document.get("table") != "tbl_sites":
        raise CountryCoverageError("SEAD site payload table identity is inconsistent")
    site_rows = _rows(site_document, "SEAD admitted sites")
    admitted_sites: dict[int, tuple[str, float, float]] = {}
    admitted_site_uuids: set[str] = set()
    for site_row in site_rows:
        site_id = _positive_integer(site_row.get("site_id"), "SEAD admitted site_id")
        site_uuid = _required_text(site_row, "site_uuid")
        if _UUID_PATTERN.fullmatch(site_uuid) is None:
            raise CountryCoverageError("SEAD admitted site_uuid is invalid")
        latitude = _coordinate(
            site_row.get("latitude_dd"), "SEAD admitted latitude", -90, 90
        )
        longitude = _coordinate(
            site_row.get("longitude_dd"), "SEAD admitted longitude", -180, 180
        )
        if site_id in admitted_sites or site_uuid in admitted_site_uuids:
            raise CountryCoverageError("SEAD admitted sites contain duplicate identity")
        admitted_sites[site_id] = (site_uuid, latitude, longitude)
        admitted_site_uuids.add(site_uuid)
    admission_table_counts = _object(
        admission_document.get("table_counts"), "SEAD admission table counts"
    )
    if _integer(
        admission_table_counts.get("tbl_sites"), "SEAD site payload row count"
    ) != len(site_rows):
        raise CountryCoverageError("SEAD site payload row count does not reconcile")

    decisions = _rows(decision_document, "SEAD country decisions", key="decisions")
    _site_partition(
        evidence,
        "sead",
        "source_reported",
        Counter({"UNASSIGNED": len(decisions)}),
    )
    governed = Counter[str]()
    decision_statuses = Counter[str]()
    decision_methods = Counter[str]()
    decision_country_codes = Counter[str]()
    seen_site_ids: set[int] = set()
    seen_site_uuids: set[str] = set()
    assigned_decision_sites: dict[int, tuple[str, float, float]] = {}
    bbox = _bbox(decision_document.get("bbox"), "SEAD country decision bbox")
    boundary_index = _boundary_component_index(boundary_collections)
    for record in decisions:
        if set(record) != {
            "decision",
            "governed_country_code",
            "latitude_dd",
            "longitude_dd",
            "site_id",
            "site_uuid",
        }:
            raise CountryCoverageError("SEAD country decision row inventory changed")
        site_id = _positive_integer(record.get("site_id"), "SEAD site identity")
        site_uuid = _required_text(record, "site_uuid")
        if _UUID_PATTERN.fullmatch(site_uuid) is None:
            raise CountryCoverageError("SEAD country decision site_uuid is invalid")
        if site_id in seen_site_ids or site_uuid in seen_site_uuids:
            raise CountryCoverageError(
                "SEAD country decisions contain duplicate identity"
            )
        seen_site_ids.add(site_id)
        seen_site_uuids.add(site_uuid)
        decision = _object(record.get("decision"), "SEAD country decision")
        latitude = _coordinate(
            record.get("latitude_dd"), "SEAD decision latitude", -90, 90
        )
        longitude = _coordinate(
            record.get("longitude_dd"), "SEAD decision longitude", -180, 180
        )
        if not (bbox[1] <= latitude <= bbox[3] and bbox[0] <= longitude <= bbox[2]):
            raise CountryCoverageError(
                f"SEAD country decision is outside its governed bbox: {site_id}"
            )
        decision_status = _required_text(decision, "decision_status")
        decision_method = _required_text(decision, "decision_method")
        country_code = _required_text(record, "governed_country_code")
        refusal_reason = decision.get("refusal_reason")
        if decision.get("raw_country") is not None:
            raise CountryCoverageError("SEAD country decision raw_country must be null")
        recomputed = _recomputed_country_decision(
            longitude,
            latitude,
            boundary_index=boundary_index,
            boundary_digest=boundary_digest,
            boundary_version=boundary_version,
        )
        recomputed_country_code = (
            _country_code(recomputed.derived_country)
            if recomputed.decision_status == "assigned"
            else "UNASSIGNED"
        )
        expected_decision = {
            "ambiguity_reason": recomputed.ambiguity_reason,
            "boundary_artifact_digest": recomputed.boundary_artifact_digest,
            "boundary_version": recomputed.boundary_version,
            "candidate_countries": list(recomputed.candidate_countries),
            "decision_method": recomputed.decision_method,
            "decision_status": recomputed.decision_status,
            "derived_country": recomputed.derived_country,
            "raw_country": recomputed.raw_country,
            "raw_country_comparison": recomputed.raw_country_comparison,
            "refusal_reason": recomputed.refusal_reason,
        }
        if dict(decision) != expected_decision:
            raise CountryCoverageError(
                f"SEAD country decision does not match governed geometry: {site_id}"
            )
        if country_code != recomputed_country_code:
            raise CountryCoverageError(
                f"SEAD governed country does not match governed geometry: {site_id}"
            )
        decision_statuses[decision_status] += 1
        decision_methods[decision_method] += 1
        decision_country_codes[country_code] += 1
        if decision_status == "assigned":
            assigned_decision_sites[site_id] = (site_uuid, latitude, longitude)
            governed[country_code] += 1
        elif decision_status == "review":
            if country_code != "UNASSIGNED" or refusal_reason is not None:
                raise CountryCoverageError(
                    "review SEAD country decision is inconsistent"
                )
            governed["UNASSIGNED"] += 1
        elif decision_status == "unassigned":
            if (
                country_code != "UNASSIGNED"
                or refusal_reason != "outside_governed_boundaries"
            ):
                raise CountryCoverageError(
                    "unassigned SEAD country decision is inconsistent"
                )
            governed["OUTSIDE"] += 1
        else:
            raise CountryCoverageError("unsupported SEAD country decision status")
    if assigned_decision_sites != admitted_sites:
        raise CountryCoverageError(
            "SEAD admitted site identities and coordinates do not reconcile"
        )
    assignment_payload = [
        {"site_id": site_id, "country_code": country_code}
        for site_id, country_code in sorted(
            (
                _positive_integer(record.get("site_id"), "SEAD assignment site_id"),
                _required_text(record, "governed_country_code"),
            )
            for record in decisions
        )
    ]
    country_assignment_sha256 = _sha256(_sead_canonical_bytes(assignment_payload))
    _validate_sead_country_summaries(
        admission_document,
        decision_document,
        decision_count=len(decisions),
        decision_statuses=decision_statuses,
        decision_methods=decision_methods,
        decision_country_codes=decision_country_codes,
        governed=governed,
        boundary_digest=boundary_digest,
        boundary_version=boundary_version,
        country_assignment_sha256=country_assignment_sha256,
        boundary_counts=boundary_counts,
        boundary_manifest=documents["data/boundaries/raw/source_manifest.json"],
        boundary_manifest_sha256=_sha256(
            input_bytes["data/boundaries/raw/source_manifest.json"]
        ),
    )
    _validate_admission_copied_file(
        admission_document,
        relative_path="country-decisions.json",
        payload=input_bytes[SEAD_DECISIONS_PATH],
    )
    _validate_admission_copied_file(
        admission_document,
        relative_path="payloads/tbl_sites.json",
        payload=input_bytes[SEAD_SITES_PATH],
    )
    _site_partition(evidence, "sead", "governed_assignment", governed)
    claim_document = sead_claim_document
    if claim_document.get("schema_version") != "sead-chronology-claim-bundle.v1":
        raise CountryCoverageError("SEAD chronology claim schema is inconsistent")
    if claim_document.get("source_run_id") != SEAD_GOVERNED_EVIDENCE_RUN_ID:
        raise CountryCoverageError(
            "SEAD chronology claims do not bind the governed run"
        )
    if (
        claim_document.get("propagation_status") != "refused"
        or claim_document.get("propagation_reason_code")
        != "source_classification_not_accepted"
    ):
        raise CountryCoverageError(
            "SEAD chronology claims do not preserve classification refusal"
        )
    if claim_document.get("acquisition_manifest_sha256") != admission_document.get(
        "acquisition_manifest_sha256"
    ):
        raise CountryCoverageError("SEAD chronology claims do not bind the admission")
    claim_country_counts = _integer_counts(
        claim_document.get("country_counts"), "SEAD claim countries"
    )
    if set(claim_country_counts) != set(_NORDIC_COUNTRY_CODES):
        raise CountryCoverageError("SEAD claim country partitions are incomplete")
    for country in ("SE", "DK", "NO", "FI"):
        counts = evidence[("sead", "governed_assignment", country)]
        counts["accepted_records"] = counts["sites"]
        counts["unresolved_records"] = 0
        counts["excluded_records"] = 0
        counts["age_claims"] = claim_country_counts[country]
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["accepted_records"] = 0
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["age_claims"] = 0
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["unresolved_records"] = (
        governed["UNASSIGNED"]
    )
    evidence[("sead", "governed_assignment", "UNASSIGNED")]["excluded_records"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["accepted_records"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["age_claims"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["unresolved_records"] = 0
    evidence[("sead", "governed_assignment", "OUTSIDE")]["excluded_records"] = governed[
        "OUTSIDE"
    ]
    _site_partition(
        evidence,
        "sead",
        "publication",
        _geojson_country_counts(documents[SEAD_PUBLIC_SITES_PATH]),
        published=True,
    )
    for country in _NORDIC_COUNTRY_CODES:
        evidence[("sead", "publication", country)]["age_claims"] = claim_country_counts[
            country
        ]
    for country in ("UNASSIGNED", "OUTSIDE"):
        evidence[("sead", "publication", country)]["age_claims"] = 0

    _record_partition(evidence, "boundaries", "source_reported", boundary_counts)
    _record_partition(evidence, "boundaries", "governed_assignment", boundary_counts)
    _record_partition(
        evidence, "boundaries", "publication", boundary_counts, published=True
    )

    for country, path in (
        ("SE", INPUT_PATHS[10]),
        ("DK", INPUT_PATHS[11]),
        ("NO", INPUT_PATHS[12]),
        ("FI", INPUT_PATHS[13]),
    ):
        summary = documents[path]
        if _country_code(summary.get("country")) != country:
            raise CountryCoverageError(
                f"AADR summary country identity does not match partition: {country}"
            )
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

    animal_rows = _rows(documents[INPUT_PATHS[14]], "animal coverage")
    animal_counts: Counter[str] = Counter()
    animal_sites: Counter[str] = Counter()
    animal_identities: set[tuple[str, str, str]] = set()
    for row in animal_rows:
        country = _country_code(row.get("country"))
        identity = (
            country,
            _required_text(row, "species_latin_name"),
            _required_text(row, "animal_scope"),
        )
        if identity in animal_identities:
            raise CountryCoverageError(
                "animal coverage contains duplicate evidence row"
            )
        animal_identities.add(identity)
        mapped_samples = _integer(
            row.get("mapped_sample_count"), "animal mapped samples"
        )
        sample_rows = _integer(row.get("sample_row_count"), "animal sample rows")
        unresolved_samples = _integer(
            row.get("unresolved_sample_count"), "animal unresolved samples"
        )
        exact_samples = _integer(
            row.get("exact_coordinate_sample_count"), "animal exact samples"
        )
        approximate_samples = _integer(
            row.get("approximate_coordinate_sample_count"),
            "animal approximate samples",
        )
        direct_sites = _integer(
            row.get("direct_coordinate_site_count"), "animal direct sites"
        )
        geocoded_sites = _integer(
            row.get("geocoded_site_count"), "animal geocoded sites"
        )
        if sample_rows != mapped_samples + unresolved_samples:
            raise CountryCoverageError("animal sample disposition does not reconcile")
        if mapped_samples != exact_samples + approximate_samples:
            raise CountryCoverageError("animal coordinate evidence does not reconcile")
        if mapped_samples != direct_sites + geocoded_sites:
            raise CountryCoverageError("animal mapped site evidence does not reconcile")
        for field in (
            "sample_lineage_backed_sample_count",
            "site_evidence_backed_sample_count",
            "chronology_provenance_backed_sample_count",
            "coordinate_provenance_backed_sample_count",
        ):
            if _integer(row.get(field), f"animal {field}") != mapped_samples:
                raise CountryCoverageError("animal provenance totals do not reconcile")
        animal_counts[country] += mapped_samples
        animal_sites[country] += direct_sites
    animal_partitions = ("SE", "DK", "NO", "FI") + tuple(
        country
        for country in ("UNASSIGNED", "OUTSIDE")
        if country in animal_counts or country in animal_sites
    )
    for country in animal_partitions:
        evidence[("animal_adna", "publication", country)] = {
            **_empty_counts(),
            "published_records": animal_counts[country],
            "samples": animal_counts[country],
            "sites": animal_sites[country],
        }
    return evidence


def _validate_sead_country_summaries(
    admission: Mapping[str, object],
    decisions: Mapping[str, object],
    *,
    decision_count: int,
    decision_statuses: Mapping[str, int],
    decision_methods: Mapping[str, int],
    decision_country_codes: Mapping[str, int],
    governed: Mapping[str, int],
    boundary_digest: str,
    boundary_version: str,
    country_assignment_sha256: str,
    boundary_counts: Mapping[str, int],
    boundary_manifest: Mapping[str, object],
    boundary_manifest_sha256: str,
) -> None:
    if admission.get("source_family") != "sead":
        raise CountryCoverageError("SEAD admission source family is inconsistent")
    _require_sha256_id(
        _required_text(admission, "scope_id"), "SEAD admission scope identity"
    )
    _require_sha256_id(
        _required_text(admission, "build_id"), "SEAD admission build identity"
    )
    if admission.get("scope_id") != SEAD_GOVERNED_EVIDENCE_SCOPE_ID:
        raise CountryCoverageError("SEAD admission governed scope identity changed")
    declared_scope = _object(admission.get("declared_scope"), "SEAD declared scope")
    if (
        declared_scope.get("scope_key") != "full_evidence_relations"
        or declared_scope.get("table_count") != 61
        or declared_scope.get("join_count") != 86
    ):
        raise CountryCoverageError("SEAD admission is not the full evidence scope")
    if admission.get("run_id") != SEAD_GOVERNED_EVIDENCE_RUN_ID:
        raise CountryCoverageError("SEAD admission governed run identity changed")
    if admission.get("parent_run_id") != decisions.get("run_id"):
        raise CountryCoverageError(
            "SEAD admission and country decisions disagree on parent run identity"
        )
    authority = _object(decisions.get("boundary_authority"), "boundary authority")
    if authority.get("artifact_digest") != boundary_digest:
        raise CountryCoverageError("SEAD boundary authority digest is inconsistent")
    if authority.get("normalized_artifact_sha256") != boundary_digest.removeprefix(
        "sha256:"
    ):
        raise CountryCoverageError("SEAD normalized boundary digest is inconsistent")
    if authority.get("version") != boundary_version.removeprefix("natural-earth:"):
        raise CountryCoverageError("SEAD boundary authority version is inconsistent")
    if authority.get("manifest_sha256") != boundary_manifest_sha256:
        raise CountryCoverageError("SEAD boundary manifest digest is inconsistent")
    manifest_artifacts = _object(
        boundary_manifest.get("country_artifacts"), "boundary country artifacts"
    )
    expected_country_digests = {
        _CODE_TO_NAME[code]: _required_text(
            _object(manifest_artifacts[_CODE_TO_NAME[code]], "boundary artifact"),
            "sha256",
        )
        for code in _NORDIC_COUNTRY_CODES
    }
    if authority.get("country_artifact_sha256") != dict(
        sorted(expected_country_digests.items())
    ):
        raise CountryCoverageError("SEAD country boundary digests are inconsistent")
    accounting = _object(admission.get("country_accounting"), "country accounting")
    _require_sha256_id(
        _required_text(accounting, "boundary_authority_id"),
        "SEAD boundary authority identity",
    )
    if accounting.get("boundary_authority_id") != authority.get("authority_id"):
        raise CountryCoverageError("SEAD boundary authority identity is inconsistent")
    if accounting.get("country_assignment_sha256") != country_assignment_sha256:
        raise CountryCoverageError("SEAD country assignment digest does not reconcile")

    expected_statuses = dict(sorted(decision_statuses.items()))
    if (
        _integer_counts(decisions.get("decision_status_counts"), "decision statuses")
        != expected_statuses
    ):
        raise CountryCoverageError("SEAD decision status counts do not reconcile")
    expected_methods = dict(sorted(decision_methods.items()))
    if (
        _integer_counts(decisions.get("decision_method_counts"), "decision methods")
        != expected_methods
    ):
        raise CountryCoverageError("SEAD decision method counts do not reconcile")
    expected_country_codes = dict(sorted(decision_country_codes.items()))
    if (
        _integer_counts(decisions.get("country_counts"), "decision countries")
        != expected_country_codes
    ):
        raise CountryCoverageError("SEAD decision country counts do not reconcile")
    if (
        _integer(decisions.get("bbox_site_count"), "SEAD bbox site count")
        != decision_count
    ):
        raise CountryCoverageError("SEAD bbox site count does not reconcile")

    nordic_counts = {
        country: int(governed.get(country, 0)) for country in ("SE", "DK", "NO", "FI")
    }
    expected_accounting = {
        "bbox_site_count": decision_count,
        "admitted_site_count": sum(nordic_counts.values()),
        "review_site_count": int(decision_statuses.get("review", 0)),
        "unassigned_site_count": int(decision_statuses.get("unassigned", 0)),
        "scope_excluded_count": int(decision_statuses.get("review", 0))
        + int(decision_statuses.get("unassigned", 0)),
    }
    for field, expected in expected_accounting.items():
        if _integer(accounting.get(field), f"SEAD {field}") != expected:
            raise CountryCoverageError(f"SEAD admission {field} does not reconcile")
    if (
        _integer_counts(accounting.get("country_counts"), "admitted country counts")
        != nordic_counts
    ):
        raise CountryCoverageError("SEAD admission country counts do not reconcile")
    if dict(boundary_counts) != dict.fromkeys(_NORDIC_COUNTRY_CODES, 1):
        raise CountryCoverageError("SEAD governed boundary inventory is inconsistent")
    if accounting.get("reconciles") is not True:
        raise CountryCoverageError(
            "SEAD admission country accounting is not reconciled"
        )


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
    collection: Mapping[str, object],
    documents: Mapping[str, Mapping[str, object]],
    input_bytes: Mapping[str, bytes],
) -> dict[str, str]:
    source_hashes = _object(collection.get("source_hashes"), "source hashes")
    result = {
        source: _sha256_id_from_raw(
            _required_text(_object(source_hashes[source], source), "snapshot_sha256"),
            f"{source} source snapshot",
        )
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
    result["neotoma"] = _require_sha256_id(
        _required_text(
            documents["data/neotoma/relational/reconciliation.json"],
            "source_snapshot_id",
        ),
        "Neotoma source snapshot",
    )
    result["sead"] = _require_sha256_id(
        _required_text(documents[INPUT_PATHS[5]], "acquisition_bundle_sha256"),
        "SEAD acquisition bundle",
    )
    result["animal_adna"] = f"sha256:{_sha256(input_bytes[INPUT_PATHS[14]])}"
    return result


def _site_partition(
    evidence: dict[tuple[str, str, str], dict[str, int | None]],
    source: str,
    dimension: str,
    values: Mapping[str, int],
    *,
    published: bool = False,
) -> None:
    unknown = set(values) - set(COUNTRIES)
    if unknown:
        raise CountryCoverageError(
            f"{source} {dimension} contains unsupported country partitions: "
            f"{sorted(unknown)}"
        )
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
    unknown = set(values) - set(COUNTRIES)
    if unknown:
        raise CountryCoverageError(
            f"{source} {dimension} contains unsupported country partitions: "
            f"{sorted(unknown)}"
        )
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
