"""Neotoma relational evidence projection."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
import hashlib
from pathlib import Path
from typing import cast

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SOURCE_NODE_CONFIG_DIGEST,
    SourceNodeContext,
    derive_neotoma_source_chronology_nodes,
)
from bijux_pollenomics.evidence.sources.neotoma import (
    read_validated_neotoma_relational_manifest,
)
from bijux_pollenomics.reporting.source_chronology import (
    build_source_chronology_atlas_projection,
)

from .constants import _UNAVAILABLE_CLASSIFICATION, _UNAVAILABLE_RELATION
from .io import (
    _decode_json_object,
    _mapping,
    _read_regular_bytes,
    _required_text,
    _safe_relative_path,
)
from .records import (
    _compact_rows_by_site,
    _features,
    _row_table,
    _set_feature_record_id,
    _unavailable,
    _unique_rows,
)


def _project_neotoma(
    context_root: Path,
    layer: MutableMapping[str, object],
) -> tuple[
    list[dict[str, object]],
    dict[str, object],
    list[dict[str, object]],
]:
    relational_root = context_root / "neotoma" / "relational"
    manifest = read_validated_neotoma_relational_manifest(relational_root.absolute())
    loaded_surfaces = {
        name: _load_neotoma_surface(relational_root, manifest, name)
        for name in (
            "sites",
            "collection_units",
            "datasets",
            "samples",
            "age_claims",
            "variables",
            "observations",
        )
    }
    surfaces = {name: loaded[0] for name, loaded in loaded_surfaces.items()}
    sites = _unique_rows(
        surfaces["sites"],
        "site_id",
        "Neotoma sites",
    )
    collection_rows = _compact_rows_by_site(
        surfaces["collection_units"],
        fields=("collection_unit_id", "source_collection_unit_id", "source_payload"),
        label="Neotoma collection unit",
    )
    dataset_rows = _compact_rows_by_site(
        surfaces["datasets"],
        fields=(
            "dataset_id",
            "collection_unit_id",
            "source_dataset_id",
            "source_payload",
        ),
        label="Neotoma dataset",
    )
    sample_rows = _compact_rows_by_site(
        surfaces["samples"],
        fields=(
            "sample_id",
            "collection_unit_id",
            "dataset_id",
            "source_sample_id",
            "source_analysis_unit_id",
            "source_analysis_unit_name",
            "source_sample_name",
            "source_igsn",
            "source_depth",
            "source_thickness",
            "source_sample_analysts",
            "source_payload",
        ),
        label="Neotoma sample",
    )
    age_fields = (
        "chronology_claim_id",
        "subject_type",
        "subject_id",
        "source_record_id",
        "chronology_id",
        "chronology_name",
        "collection_unit_id",
        "dataset_id",
        "source_age_type",
        "source_age_unit",
        "source_age_value",
        "source_age_younger",
        "source_age_older",
        "younger_bp",
        "older_bp",
        "calibration_status",
        "comparability_status",
        "admission_reason",
        "refusal_reason",
        "is_default_chronology",
        "provenance_record_id",
        "source_relation_path",
    )
    age_rows = _compact_rows_by_site(
        surfaces["age_claims"],
        fields=age_fields,
        label="Neotoma age claim",
    )
    observation_fields = (
        "observation_id",
        "sample_id",
        "variable_id",
        "source_taxon_id",
        "source_value",
        "source_unit",
        "source_denominator",
        "denominator_status",
        "detection_status",
        "source_context",
        "source_ecological_group",
        "source_element",
        "source_element_type",
        "aggregation_key",
        "unit_family",
        "source_part_number",
    )
    observation_rows = _compact_rows_by_site(
        surfaces["observations"],
        fields=observation_fields,
        label="Neotoma observation",
    )
    observation_part_numbers = {
        _required_text(row.get("observation_id"), "Neotoma observation ID"): part
        for row, part in zip(
            surfaces["observations"],
            loaded_surfaces["observations"][1],
            strict=True,
        )
    }
    for rows in observation_rows.values():
        for row in rows:
            row[-1] = observation_part_numbers[
                _required_text(row[0], "Neotoma observation ID")
            ]
    variable_fields = (
        "variable_id",
        "source_taxon_id",
        "source_reported_name",
        "source_semantics",
        "source_units",
    )
    variables = _unique_rows(
        surfaces["variables"],
        "variable_id",
        "Neotoma variables",
    )
    site_ids = set(sites)
    for label, grouped_rows in (
        ("collection units", collection_rows),
        ("datasets", dataset_rows),
        ("samples", sample_rows),
        ("age claims", age_rows),
        ("observations", observation_rows),
    ):
        unknown_site_ids = sorted(set(grouped_rows) - site_ids)
        if unknown_site_ids:
            raise ValueError(
                f"Neotoma {label} reference unknown sites: {unknown_site_ids[:5]}"
            )
    referenced_variable_ids = {
        _required_text(row[2], "Neotoma observation variable ID")
        for rows in observation_rows.values()
        for row in rows
    }
    if referenced_variable_ids != set(variables):
        raise ValueError("Neotoma variable and observation identities do not reconcile")

    source_snapshot_id = _required_text(
        manifest.get("source_snapshot_id"), "Neotoma source snapshot ID"
    )
    build_id = _required_text(manifest.get("build_id"), "Neotoma build ID")
    materialization_sha256 = _required_text(
        manifest.get("materialization_sha256"), "Neotoma materialization SHA-256"
    )
    records: list[dict[str, object]] = []
    observed_sites: set[str] = set()
    features = _features(layer)
    for feature in features:
        source_site_id = _required_text(
            feature.get("evidence_row_id"), "Neotoma feature evidence_row_id"
        )
        site_id = f"neotoma:site:{source_site_id}"
        site = sites.get(site_id)
        if site is None:
            raise ValueError(f"Neotoma map feature has no relational site: {site_id}")
        _set_feature_record_id(feature, site_id)
        if site_id in observed_sites:
            raise ValueError(f"Neotoma map features duplicate site identity: {site_id}")
        observed_sites.add(site_id)
        site_age_rows = age_rows[site_id]
        site_observation_rows = observation_rows[site_id]
        site_variable_ids = sorted(
            {
                _required_text(row[2], "Neotoma observation variable ID")
                for row in site_observation_rows
            }
        )
        missing_variables = [
            variable_id
            for variable_id in site_variable_ids
            if variable_id not in variables
        ]
        if missing_variables:
            raise ValueError(
                f"Neotoma observations reference unknown variables: {missing_variables[:5]}"
            )
        site_variable_rows = [
            [variables[variable_id].get(field) for field in variable_fields]
            for variable_id in site_variable_ids
        ]
        records.append(
            {
                "record_id": site_id,
                "tabs": {
                    "overview": {
                        "source_family": "neotoma",
                        "site_id": site_id,
                        "source_site_id": source_site_id,
                        "country_code": site.get("country_code"),
                        "country_decision_status": site.get("country_decision_status"),
                    },
                    "samples": {
                        "collection_units": _row_table(
                            (
                                "collection_unit_id",
                                "source_collection_unit_id",
                                "source_payload",
                            ),
                            collection_rows[site_id],
                        ),
                        "datasets": _row_table(
                            (
                                "dataset_id",
                                "collection_unit_id",
                                "source_dataset_id",
                                "source_payload",
                            ),
                            dataset_rows[site_id],
                        ),
                        "samples": _row_table(
                            (
                                "sample_id",
                                "collection_unit_id",
                                "dataset_id",
                                "source_sample_id",
                                "source_analysis_unit_id",
                                "source_analysis_unit_name",
                                "source_sample_name",
                                "source_igsn",
                                "source_depth",
                                "source_thickness",
                                "source_sample_analysts",
                                "source_payload",
                            ),
                            sample_rows[site_id],
                        ),
                    },
                    "chronology": (
                        {
                            **_row_table(
                                age_fields,
                                site_age_rows,
                                identifier_prefixes={
                                    "chronology_claim_id": "neotoma:age-claim:",
                                    "subject_id": "neotoma:sample:",
                                    "source_record_id": "neotoma:sample:",
                                    "chronology_id": "neotoma:chronology:",
                                    "collection_unit_id": "neotoma:collection-unit:",
                                    "dataset_id": "neotoma:dataset:",
                                },
                            ),
                            "interval_semantics": "[younger_bp, older_bp]",
                            "null_semantics": "source null remains null",
                            "selection_posture": "all source age assignments retained",
                        }
                        if site_age_rows
                        else _unavailable("neotoma_site_age_claims_not_available")
                    ),
                    "pollen_composition": (
                        {
                            **_row_table(
                                observation_fields,
                                site_observation_rows,
                                identifier_prefixes={
                                    "observation_id": "neotoma:observation:",
                                    "sample_id": "neotoma:sample:",
                                    "variable_id": "neotoma:variable:",
                                    "aggregation_key": "neotoma:exact-unit:",
                                },
                            ),
                            "variables": _row_table(
                                variable_fields,
                                site_variable_rows,
                                identifier_prefixes={
                                    "variable_id": "neotoma:variable:"
                                },
                            ),
                            "aggregation_posture": "source rows retained without cross-unit summing",
                            "classification_status": "not_accepted",
                        }
                        if site_observation_rows
                        else _unavailable("neotoma_site_observations_not_available")
                    ),
                    "relation": dict(_UNAVAILABLE_RELATION),
                    "classification": dict(_UNAVAILABLE_CLASSIFICATION),
                    "provenance": {
                        "source_snapshot_id": source_snapshot_id,
                        "build_id": build_id,
                        "materialization_sha256": materialization_sha256,
                        "record_locator": f"surfaces/sites#site_id={site_id}",
                        "compact_lineage_path": "data/neotoma/review/compact_relational_lineage.json",
                        "observation_locator_contract": "surfaces/observations/part-{source_part_number:05d}.json#observation_id={observation_id}",
                    },
                },
            }
        )
    if observed_sites != set(sites):
        raise ValueError("Neotoma map and relational site identities do not reconcile")
    detail_row_counts = {
        "collection_units": sum(len(rows) for rows in collection_rows.values()),
        "datasets": sum(len(rows) for rows in dataset_rows.values()),
        "samples": sum(len(rows) for rows in sample_rows.values()),
        "age_claims": sum(len(rows) for rows in age_rows.values()),
        "observations": sum(len(rows) for rows in observation_rows.values()),
        "variables": len(variables),
    }
    source_node_result = derive_neotoma_source_chronology_nodes(
        observations=surfaces["observations"],
        samples=surfaces["samples"],
        sites=surfaces["sites"],
        variables=surfaces["variables"],
        chronologies=surfaces["age_claims"],
        context=SourceNodeContext(
            config_digest=SOURCE_NODE_CONFIG_DIGEST,
            source_snapshot_id=source_snapshot_id,
            build_id=build_id,
        ),
    )
    source_projection = build_source_chronology_atlas_projection(
        source_node_result,
        detail_record_ids=sites.keys(),
    )
    accounting = {
        "source_feature_count": len(features),
        "source_site_denominator": len(sites),
        "projected_site_count": len(records),
        "unprojected_source_site_count": len(sites) - len(records),
        "source_snapshot_id": source_snapshot_id,
        "build_id": build_id,
        "materialization_sha256": materialization_sha256,
        "detail_row_counts": detail_row_counts,
        "detail_row_denominators": dict(detail_row_counts),
        "source_chronology": source_projection.reconciliation,
    }
    return (
        records,
        accounting,
        [dict(layer) for layer in source_projection.point_layers],
    )


def _load_neotoma_surface(
    root: Path, manifest: Mapping[str, object], surface_name: str
) -> tuple[list[Mapping[str, object]], tuple[int, ...]]:
    surfaces = _mapping(manifest.get("surfaces"), "Neotoma surfaces")
    surface = _mapping(surfaces.get(surface_name), f"Neotoma {surface_name} surface")
    parts = surface.get("parts")
    if not isinstance(parts, list) or any(
        not isinstance(row, Mapping) for row in parts
    ):
        raise ValueError(f"Neotoma {surface_name} parts are invalid")
    rows: list[Mapping[str, object]] = []
    part_numbers: list[int] = []
    for part_number, part_row in enumerate(
        cast(list[Mapping[str, object]], parts), start=1
    ):
        relative_path = _safe_relative_path(part_row.get("path"))
        expected_digest = _required_text(
            part_row.get("sha256"), f"Neotoma {relative_path} SHA-256"
        )
        payload_bytes = _read_regular_bytes(root / relative_path, relative_path)
        if hashlib.sha256(payload_bytes).hexdigest() != expected_digest:
            raise ValueError(f"Neotoma surface digest changed: {relative_path}")
        payload = _decode_json_object(payload_bytes, relative_path)
        raw_rows = payload.get("rows")
        if not isinstance(raw_rows, list) or any(
            not isinstance(row, Mapping) for row in raw_rows
        ):
            raise ValueError(f"Neotoma surface rows are invalid: {relative_path}")
        if payload.get("row_count") != len(raw_rows):
            raise ValueError(f"Neotoma surface row count changed: {relative_path}")
        rows.extend(cast(list[Mapping[str, object]], raw_rows))
        part_numbers.extend([part_number] * len(raw_rows))
    if surface.get("row_count") != len(rows):
        raise ValueError(f"Neotoma {surface_name} row count does not reconcile")
    return rows, tuple(part_numbers)
