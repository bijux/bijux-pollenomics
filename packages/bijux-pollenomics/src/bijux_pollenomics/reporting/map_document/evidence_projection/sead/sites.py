"""Nordic SEAD site admission and map-feature reconciliation."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, Sequence
from typing import cast

from ..io import (
    _identifier_text,
    _mapping,
    _numeric_text_key,
    _read_json_object,
    _required_text,
)
from ..records import _features, _set_feature_record_id, _unique_rows
from .models import ClaimIndex, EvidenceBundle, ObservationIndex, SiteIndex


def index_sites(
    bundle: EvidenceBundle,
    claims: ClaimIndex,
    observations: ObservationIndex,
    layers: Sequence[MutableMapping[str, object]],
) -> SiteIndex:
    """Reconcile normalized sites, country decisions, and atlas features."""
    site_artifact = _read_json_object(
        bundle.context_root
        / "sead"
        / "normalized"
        / "nordic_environmental_sites.geojson",
        "SEAD Nordic site artifact",
    )
    if site_artifact.get("type") != "FeatureCollection":
        raise ValueError("SEAD Nordic site artifact is not a FeatureCollection")
    raw_site_features = site_artifact.get("features")
    if not isinstance(raw_site_features, list) or any(
        not isinstance(row, Mapping) for row in raw_site_features
    ):
        raise ValueError("SEAD Nordic site features must be object rows")
    site_rows: list[Mapping[str, object]] = []
    for raw_feature in cast(list[Mapping[str, object]], raw_site_features):
        properties = _mapping(
            raw_feature.get("properties"), "SEAD Nordic site properties"
        )
        if (
            properties.get("source") != "SEAD"
            or properties.get("layer_key") != "sead-sites"
        ):
            raise ValueError("SEAD Nordic site identity changed")
        site_rows.append(properties)
    sites = _unique_rows(site_rows, "record_id", "SEAD Nordic sites")
    normalized_site_uuids = {
        site_id: _required_text(row.get("site_uuid"), "SEAD normalized site UUID")
        for site_id, row in sites.items()
    }
    admitted_site_uuids = _admitted_site_uuids(bundle)
    admitted_site_ids = set(admitted_site_uuids)
    decision_rows, assigned_site_ids = _country_decisions(bundle)
    _validate_site_identity_links(admitted_site_uuids, decision_rows, claims)
    if not set(sites) <= admitted_site_ids:
        raise ValueError("SEAD normalized sites are missing from admitted site rows")
    if set(sites) != assigned_site_ids:
        raise ValueError(
            "SEAD normalized sites do not match assigned country decisions"
        )
    for site_id, site_uuid in normalized_site_uuids.items():
        if site_uuid != admitted_site_uuids[site_id]:
            raise ValueError("SEAD normalized site UUID differs from admitted site")
    unknown_claim_sites = sorted(set(claims.by_site) - set(sites))
    if unknown_claim_sites:
        raise ValueError(
            f"SEAD claims reference unknown admitted sites: {unknown_claim_sites[:5]}"
        )
    unknown_observation_sites = sorted(set(observations.by_site) - set(sites))
    if unknown_observation_sites:
        raise ValueError(
            "SEAD observations reference unknown admitted sites: "
            f"{unknown_observation_sites[:5]}"
        )
    feature_site_ids, feature_count = _bind_features(layers, sites, admitted_site_uuids)
    return SiteIndex(
        rows_by_id=sites,
        site_uuid_by_id=admitted_site_uuids,
        decision_rows=decision_rows,
        assigned_site_ids=assigned_site_ids,
        feature_site_ids=feature_site_ids,
        feature_count=feature_count,
    )


def _admitted_site_uuids(bundle: EvidenceBundle) -> dict[str, str]:
    payload = _read_json_object(
        bundle.acquisition_root / "payloads" / "tbl_sites.json",
        "SEAD admitted sites",
    )
    rows = payload.get("rows")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("SEAD admitted site rows are invalid")
    by_site: dict[str, str] = {}
    seen_site_uuids: set[str] = set()
    for row in cast(list[Mapping[str, object]], rows):
        site_id = _identifier_text(row.get("site_id"), "SEAD admitted site ID")
        site_uuid = _required_text(row.get("site_uuid"), "SEAD admitted site UUID")
        if site_id in by_site:
            raise ValueError(f"SEAD admitted site ID is duplicated: {site_id}")
        if site_uuid in seen_site_uuids:
            raise ValueError(f"SEAD admitted site UUID is duplicated: {site_uuid}")
        by_site[site_id] = site_uuid
        seen_site_uuids.add(site_uuid)
    return by_site


def _country_decisions(
    bundle: EvidenceBundle,
) -> tuple[list[Mapping[str, object]], set[str]]:
    document = _read_json_object(
        bundle.acquisition_root / "country-decisions.json", "SEAD country decisions"
    )
    rows = document.get("decisions")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise ValueError("SEAD country decisions must be object rows")
    decision_rows = cast(list[Mapping[str, object]], rows)
    by_site = _unique_rows(decision_rows, "site_id", "SEAD decisions")
    assigned_site_ids = {
        site_id
        for site_id, row in by_site.items()
        if _mapping(row.get("decision"), "SEAD country decision").get("decision_status")
        == "assigned"
        and row.get("governed_country_code") in {"SE", "DK", "NO", "FI"}
    }
    return decision_rows, assigned_site_ids


def _validate_site_identity_links(
    admitted_site_uuids: Mapping[str, str],
    decision_rows: Sequence[Mapping[str, object]],
    claims: ClaimIndex,
) -> None:
    for row in decision_rows:
        site_id = _identifier_text(row.get("site_id"), "SEAD decision site ID")
        site_uuid = _required_text(row.get("site_uuid"), "SEAD decision site UUID")
        admitted_uuid = admitted_site_uuids.get(site_id)
        if admitted_uuid is not None and admitted_uuid != site_uuid:
            raise ValueError("SEAD decision site UUID differs from admitted site")
    for site_id, site_claims in claims.by_site.items():
        expected_uuid = admitted_site_uuids.get(site_id)
        if expected_uuid is None:
            continue
        for claim in site_claims:
            site_uuid = _required_text(claim.get("site_uuid"), "SEAD claim site UUID")
            if site_uuid != expected_uuid:
                raise ValueError("SEAD claim site UUID differs from admitted site")


def _bind_features(
    layers: Sequence[MutableMapping[str, object]],
    sites: Mapping[str, Mapping[str, object]],
    site_uuid_by_id: Mapping[str, str],
) -> tuple[set[str], int]:
    feature_site_ids: set[str] = set()
    feature_count = 0
    for layer in layers:
        for feature in _features(layer):
            native_id = _required_text(
                feature.get("evidence_row_id"), "SEAD feature evidence_row_id"
            )
            source_site_id = native_id.split(":", 1)[0]
            if source_site_id not in sites:
                raise ValueError(
                    f"SEAD map feature has no governed Nordic site: {source_site_id}"
                )
            feature_site_uuid = _required_text(
                feature.get("site_uuid"), "SEAD feature site UUID"
            )
            if feature_site_uuid != site_uuid_by_id[source_site_id]:
                raise ValueError("SEAD feature site UUID differs from admitted site")
            _set_feature_record_id(feature, f"sead:site:{source_site_id}")
            feature["site_uuid"] = feature_site_uuid
            feature_site_ids.add(source_site_id)
            feature_count += 1
    if feature_site_ids != set(sites):
        missing = sorted(set(sites) - feature_site_ids, key=_numeric_text_key)
        raise ValueError(
            f"SEAD atlas does not expose every governed site: {missing[:5]}"
        )
    return feature_site_ids, feature_count
