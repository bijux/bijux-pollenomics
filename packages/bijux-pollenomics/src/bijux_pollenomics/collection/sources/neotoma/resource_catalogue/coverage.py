"""Project exact native resource/version coverage without merging scientific epochs."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict
import math
from pathlib import Path
from typing import Any

from ..capture.receipts import _object
from ..capture.resources import NeotomaResourceSpec, NeotomaRetainedSource
from ..capture.resources.frozen import parse_neotoma_frozen_snapshot
from ..capture.resources.models import DEVELOPMENT_ROLES
from ..capture.resources.protocol import identity, resource_key
from ..country.decisions import build_neotoma_context_country_decisions
from ..relational.country import country_attribution
from .custody import CatalogueSources, prepare_catalogue_sources
from .source_projection import (
    _same,
    catalogue_accounts,
    inventory_scope,
    method_capability,
    original_epoch,
    related_facets,
)


def _native_counts(samples: object, chronologies: object) -> dict[str, Any]:
    sample_rows = samples if isinstance(samples, list) else []
    datums = [
        datum
        for sample in sample_rows
        if isinstance(sample, dict)
        for datum in sample.get("datum", [])
        if isinstance(datum, dict)
    ]
    chronology_rows = chronologies if isinstance(chronologies, list) else []
    controls = [
        control
        for row in chronology_rows
        if isinstance(row, dict) and isinstance(row.get("chronology"), dict)
        for control in row["chronology"].get("chroncontrols", [])
        if isinstance(control, dict)
    ]
    identified_samples = [
        row["sampleid"]
        for row in sample_rows
        if isinstance(row, dict)
        and type(row.get("sampleid")) is int
        and row["sampleid"] > 0
    ]
    identified_controls = [
        row["chroncontrolid"]
        for row in controls
        if type(row.get("chroncontrolid")) is int and row["chroncontrolid"] > 0
    ]
    units = {
        datum.get("units")
        for datum in datums
        if datum.get("units") is None or isinstance(datum.get("units"), str)
    }
    return {
        "raw_sample_rows": len(samples) if isinstance(samples, list) else None,
        "sample_population": "array"
        if isinstance(samples, list)
        else "null_or_unavailable",
        "identified_sample_rows": len(identified_samples),
        "distinct_identified_samples": len(set(identified_samples)),
        "raw_datum_rows": len(datums) if isinstance(samples, list) else None,
        "datum_rows_with_values": sum(
            datum.get("value") is not None for datum in datums
        ),
        "numeric_value_rows": sum(
            type(datum.get("value")) is int
            or (type(datum.get("value")) is float and math.isfinite(datum["value"]))
            for datum in datums
        ),
        "datum_rows_without_taxonid": sum("taxonid" not in datum for datum in datums),
        "raw_chronology_rows": len(chronologies)
        if isinstance(chronologies, list)
        else None,
        "raw_chroncontrol_rows": len(controls),
        "distinct_identified_chroncontrols": len(set(identified_controls)),
        "source_units": sorted(
            units, key=lambda value: (value is not None, str(value))
        ),
        "dated_measurements": None,
        "dated_measurements_scope": "Not inferred from sample/datum placeholders or control membership rows",
        "biological_independence": "not_asserted",
        "units_interpreted": False,
    }


def _version(
    sources: CatalogueSources, resource: NeotomaResourceSpec, version: str
) -> dict[str, Any]:
    key = resource_key(resource, version)
    selected = sources.selected.get(key)
    if selected is None:
        return {
            "acquisition_status": "not_attempted_exposure_role"
            if resource.exposure_role not in DEVELOPMENT_ROLES
            else "not_attempted_pending_capture",
            "source_terminal_status": None,
            "qualification_status": "not_qualified",
            "source": None,
            "native_counts": None,
            "absence_certified": False,
        }
    digest, entry = selected
    if not _same(entry["identity"], identity(resource)):
        raise ValueError(
            "Selected resource capture identity differs from its roster owner"
        )
    source, body = sources.source(digest, entry)
    status = entry["terminal_status"]
    result: dict[str, Any] = {
        "acquisition_status": status,
        "source_terminal_status": status,
        "qualification_status": "not_qualified",
        "source": source,
        "native_counts": None,
        "absence_certified": False,
        "attempt_count": len(entry["attempts"]),
    }
    for field in (
        "reason",
        "http_status",
        "summary",
        "predecessor_result",
        "reused_from",
    ):
        if field in entry:
            result[field] = entry[field]
    if resource.exposure_role not in DEVELOPMENT_ROLES:
        return result
    if version == "current" and status in {"parsed_native", "reused_qualified_native"}:
        if body is None:
            raise ValueError("Qualified current resource has no authenticated body")
        native = _object(body)["data"][0]["site"]["collectionunit"]
        result.update(
            qualification_status="parsed_native",
            native_counts=_native_counts(
                native["dataset"].get("samples"), native.get("chronologies")
            ),
        )
    elif version == "doi_frozen":
        qualification = sources.qualifications[key]
        result["qualification_status"] = qualification["qualification_status"]
        if "reason" in qualification:
            result["qualification_reason"] = qualification["reason"]
        snapshot_qualification = sources.source_snapshots[key]
        result["snapshot_qualification_status"] = snapshot_qualification[
            "qualification_status"
        ]
        if "strict_current_binding_status" in snapshot_qualification:
            result["strict_current_binding_status"] = snapshot_qualification[
                "strict_current_binding_status"
            ]
        if snapshot_qualification["qualification_status"] == "parsed_frozen_snapshot":
            if body is None:
                raise ValueError("Qualified frozen resource has no authenticated body")
            snapshot = parse_neotoma_frozen_snapshot(
                resource, body, expected_body_sha256=source["body_sha256"]
            )
            result.update(
                native_counts=_native_counts(
                    snapshot.native.samples, snapshot.native.chronologies
                ),
                frozen_parser_profile=snapshot.native.parser_profile,
                native_snapshot_metadata=snapshot.native.dataset,
                snapshot_database_metadata=snapshot.database_metadata,
                snapshot_date_inferred=False,
                original_publication_identity="not_asserted",
            )
    return result


def build_neotoma_resource_catalogue(
    *,
    roster_path: Path,
    expected_roster_sha256: str,
    metadata_captures: Mapping[str, Path],
    resource_captures: Mapping[str, Path],
    source_captures: Mapping[str, Path] | None = None,
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
    original_relational_root: Path | None = None,
    country_boundaries: Mapping[str, Mapping[str, object]] | None = None,
    policy_sources: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Join the exact declared roster to selected captures and separate source epochs.

    Direct resource captures must be disjoint. Ancestor resolvers authenticate
    reused bodies without introducing extra resource/version rows. Native source
    bodies are decoded one at a time; only compact counts and locators persist.
    """
    sources = prepare_catalogue_sources(
        roster_path=roster_path,
        expected_roster_sha256=expected_roster_sha256,
        metadata_captures=metadata_captures,
        resource_captures=resource_captures,
        source_captures=source_captures,
        retained_sources=retained_sources,
        original_relational_root=original_relational_root,
    )
    expected_keys = {
        f"dataset-{row['dataset_id']}-{version}"
        for row in sources.roster["resources"]
        for version in ("current", "doi_frozen")
    }
    if set(sources.selected) - expected_keys:
        raise ValueError("Selected capture contains an unexpected resource/version")
    policies = list(
        policy_sources
        if policy_sources is not None
        else sources.roster.get("policy_sources", [])
    )
    if not policies or any(
        not isinstance(url, str) or not url.startswith("https://") for url in policies
    ):
        raise ValueError("Catalogue public data policy references are unavailable")
    decisions = (
        build_neotoma_context_country_decisions(sources.sites, country_boundaries)
        if country_boundaries
        else {}
    )
    resources = []
    for row in sorted(
        sources.roster["resources"], key=lambda value: value["dataset_id"]
    ):
        role = row["exposure_roles"]["current"]
        native = sources.metadata[row["dataset_id"]]
        resource = NeotomaResourceSpec(
            row["dataset_id"],
            row["site_id"],
            row["collection_unit_id"],
            row["dataset_type"],
            row["database"],
            role,
            row["metadata_locator"]["response_sha256"],
            row["metadata_locator"]["json_pointer"],
        )
        original = original_epoch(sources.original_epochs, resource.dataset_id)
        decision = decisions.get(str(resource.site_id))
        country: dict[str, Any] = (
            asdict(country_attribution(decision))
            if decision is not None
            else {
                "final_country_code": "UNASSIGNED",
                "decision_status": "unassigned",
                "refusal_reason": "missing_country_boundary_authority",
            }
        )
        if "candidate_countries" in country:
            country["candidate_countries"] = list(country["candidate_countries"])
        resources.append(
            {
                "dataset_id": resource.dataset_id,
                "site_id": resource.site_id,
                "collection_unit_id": resource.collection_unit_id,
                "dataset_type": resource.dataset_type,
                "database": resource.database,
                "exposure_role": role,
                "role_authority": row.get("role_authority"),
                "metadata": native,
                "country": country,
                "rights": {
                    "available_public_data_license": "CC BY 4.0",
                    "policy_sources": policies,
                    "provider": "Neotoma Paleoecology Database",
                    "constituent_database": resource.database,
                    "dataset_doi_values": row["dataset_doi_values"],
                    "investigator_metadata": native["native_dataset"].get(
                        "datasetpi", []
                    ),
                    "publication_identity": "Not inferred from a DOI-frozen response",
                    "scope": "Available public data; no private-workbook rights or unreturned-source availability inferred",
                },
                "method_capability": method_capability(resource.dataset_type),
                "original_epoch": original,
                "versions": {
                    version: _version(sources, resource, version)
                    for version in ("current", "doi_frozen")
                },
            }
        )
    return {
        "schema_version": "neotoma-resource-catalogue.v1",
        "source_family": "neotoma",
        "inventory_scope": inventory_scope(),
        "expected_roster_sha256": expected_roster_sha256,
        **catalogue_accounts(resources),
        "resources": resources,
        "capture_descriptors": sources.descriptors,
        "selected_resource_capture_manifest_sha256": sorted(resource_captures),
        "metadata_capture_manifest_sha256": sorted(metadata_captures),
        "related_facets": related_facets(),
    }


def verify_catalogue_source_projection(
    catalogue: dict[str, Any],
    capture_sources: Mapping[str, Path],
    retained_sources: Mapping[str, NeotomaRetainedSource] | None = None,
) -> None:
    """Recompute version facts from retained source buffers during raw readback."""
    from ..capture.resources import replay_neotoma_resource_capture
    from ..capture.resources.frozen import (
        qualify_neotoma_frozen_capture,
        qualify_neotoma_frozen_snapshot_capture,
    )
    from .custody import pinned_object

    selected: dict[str, tuple[str, dict[str, Any]]] = {}
    qualifications: dict[str, dict[str, Any]] = {}
    source_snapshots: dict[str, dict[str, Any]] = {}
    manifests: dict[str, dict[str, Any]] = {}
    roots = {
        digest: capture_sources[digest]
        for digest, descriptor in catalogue["capture_descriptors"].items()
        if descriptor["capture_kind"] == "resources"
    }
    for digest in catalogue["selected_resource_capture_manifest_sha256"]:
        captured = replay_neotoma_resource_capture(
            roots[digest],
            expected_manifest_sha256=digest,
            source_captures=roots,
            retained_sources=retained_sources,
        )
        for entry in captured.resources:
            if entry["resource_key"] in selected:
                raise ValueError("Duplicate catalogue source projection")
            selected[entry["resource_key"]] = digest, entry
        qualified = qualify_neotoma_frozen_capture(
            roots[digest],
            expected_manifest_sha256=digest,
            source_captures=roots,
            retained_sources=retained_sources,
        )
        qualifications.update(
            (entry["resource_key"], entry) for entry in qualified["resources"]
        )
        snapshots = qualify_neotoma_frozen_snapshot_capture(
            roots[digest],
            expected_manifest_sha256=digest,
            source_captures=roots,
            retained_sources=retained_sources,
        )
        source_snapshots.update(
            (entry["resource_key"], entry) for entry in snapshots["resources"]
        )
    for digest, root in roots.items():
        manifests[digest] = pinned_object(
            root / "capture-manifest.json", digest, 16 * 1024 * 1024
        )
    sources = CatalogueSources(
        {},
        {},
        [],
        None,
        {},
        selected,
        roots,
        manifests,
        qualifications,
        retained_sources or {},
        source_snapshots,
    )
    for row in catalogue["resources"]:
        metadata = row["metadata"]["source"]
        resource = NeotomaResourceSpec(
            row["dataset_id"],
            row["site_id"],
            row["collection_unit_id"],
            row["dataset_type"],
            row["database"],
            row["exposure_role"],
            metadata["body_sha256"],
            metadata["json_pointer"],
        )
        for version in ("current", "doi_frozen"):
            if not _same(
                row["versions"][version], _version(sources, resource, version)
            ):
                raise ValueError(
                    "Catalogue version projection differs from retained source"
                )
