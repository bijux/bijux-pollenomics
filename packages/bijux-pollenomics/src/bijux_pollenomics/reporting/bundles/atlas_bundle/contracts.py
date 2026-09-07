"""Traceability and map-publication contract emission."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def publish_contracts(
    *,
    report: Any,
    geography_scope: Any,
    countries: tuple[str, ...],
    point_layers: list[dict[str, object]],
    polygon_layers: list[dict[str, object]],
    bundle_paths: Any,
    detail_projection_reconciliation: Any,
    static_assets: Any,
    animal_chronology_context: Any,
    extra_artifacts: list[tuple[str, str]],
    write_summary_json_fn: Any,
    surface: Any,
) -> tuple[Any, dict[str, object]]:
    map_policy = surface.resolve_map_scope_policy(geography_scope)
    point_traceability = surface.build_map_point_traceability(
        report=report,
        point_layers=point_layers,
    )
    write_summary_json_fn(
        bundle_paths.map_point_traceability_json_path,
        point_traceability,
    )
    bundle_paths.map_point_traceability_markdown_path.write_text(
        surface.render_map_point_traceability_markdown(point_traceability),
        encoding="utf-8",
    )
    map_publication_contract = surface.build_map_publication_contract(
        report=report,
        policy=map_policy,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
        countries=countries,
        map_html_name=bundle_paths.map_html_path.name,
        summary_json_name=bundle_paths.summary_json_path.name,
        traceability_json_name=bundle_paths.map_point_traceability_json_path.name,
    )
    map_publication_contract["static_assets"] = {
        "schema_version": static_assets.manifest["schema_version"],
        "manifest": static_assets.manifest_path.name,
        "budgets": static_assets.manifest["budgets"],
        "domains": static_assets.manifest["domains"],
    }
    if animal_chronology_context is not None:
        payload, identity = _animal_chronology_publication(
            animal_chronology_context,
            artifact_name=(
                bundle_paths.animal_sample_chronology_context_json_path.name
            ),
        )
        write_summary_json_fn(
            bundle_paths.animal_sample_chronology_context_json_path,
            payload,
        )
        map_publication_contract["animal_sample_chronology_context"] = identity
        extra_artifacts.append(
            (
                "Animal source-sample chronology accountability",
                bundle_paths.animal_sample_chronology_context_json_path.name,
            )
        )
    if detail_projection_reconciliation is not None:
        map_publication_contract["detail_projection"] = dict(
            detail_projection_reconciliation
        )
    write_summary_json_fn(
        bundle_paths.map_publication_contract_json_path,
        map_publication_contract,
    )
    bundle_paths.map_publication_contract_markdown_path.write_text(
        surface.render_map_publication_contract_markdown(map_publication_contract),
        encoding="utf-8",
    )
    return map_policy, map_publication_contract


def _animal_chronology_publication(
    projection: Any, *, artifact_name: str
) -> tuple[dict[str, object], dict[str, object]]:
    input_identity = projection.input_identity.as_dict()
    accountability = dict(projection.accountability)
    refusals = [refusal.as_dict() for refusal in projection.refusals]
    if accountability.get("input_identity") != input_identity:
        raise ValueError("animal chronology accountability input identity differs")
    if accountability.get("refusal_count") != len(refusals):
        raise ValueError("animal chronology accountability refusal count differs")
    content: dict[str, object] = {
        "schema_version": "animal-sample-chronology-context-publication.v1",
        "accountability": accountability,
        "refusals": refusals,
        "input_identity": input_identity,
    }
    content_sha256 = hashlib.sha256(
        json.dumps(
            content,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    payload = {**content, "content_sha256": content_sha256}
    return payload, {
        "artifact": artifact_name,
        "content_sha256": content_sha256,
        "input_identity_sha256": input_identity["combined_sha256"],
        "scope": accountability["scope"],
        "global_admitted_node_count": accountability["global_admitted_node_count"],
        "projected_node_count": accountability["projected_node_count"],
        "excluded_by_scope_count": accountability["excluded_by_scope_count"],
        "refusal_count": accountability["refusal_count"],
        "governed_country_rows": accountability["governed_country_rows"],
    }
