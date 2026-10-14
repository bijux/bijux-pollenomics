"""Actual public serializers retain source eligibility through external and map readers."""

from __future__ import annotations

from dataclasses import replace
import json
from types import SimpleNamespace
from typing import Any, cast

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.reporting.bundles.atlas_bundle.context import (
    extract_context_points,
)
from bijux_pollenomics.reporting.context import build_external_point_layer
from bijux_pollenomics.reporting.rendering.record_exports import (
    serialize_sample_record,
)

from ...map_document.browser_semantics.support import run_node_json, template_block
from ...rendering.test_sample_chronology_exports import _source_sample


def _record(
    posture: str = "sample_precise_interval", refusal: str = "", *, version: str = "v2"
) -> dict[str, Any]:
    sample = _source_sample(0, 0)
    sample = replace(
        sample,
        chronology=replace(
            sample.chronology, precision_posture=posture, refusal_reason_code=refusal
        ),
    )
    return serialize_sample_record(
        sample, schema_version="adna-sample-record-export." + version
    )


def _browser(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source = template_block(
        "function finiteTimeValue", "function pointFeatureInTimeWindow"
    )
    return cast(
        list[dict[str, Any]],
        run_node_json(
            source
            + "\nconsole.log(JSON.stringify("
            + json.dumps(features)
            + ".map(featureTimeAdmission)));"
        ),
    )


def _collection(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [18, 59]},
                "properties": {
                    **record,
                    "layer_key": "controlled-source",
                    "layer_label": "Controlled source",
                },
            }
        ],
    }


def _owned_locality_record() -> dict[str, Any]:
    from bijux_pollenomics.adna import AdnaChronology
    from bijux_pollenomics.adna.domain.models.localities import (
        AdnaSampleChronologySupport,
    )
    from bijux_pollenomics.reporting.rendering.record_exports import (
        serialize_locality_summary,
    )

    from ....analysis.fieldwork.ranking_examples import _locality

    locality = _locality("Controlled source locality", 59, 18, sample_count=4)
    supports = tuple(
        AdnaSampleChronologySupport(
            sample_id=identifier,
            chronology=AdnaChronology(
                original_text="retained source interval",
                time_start_bp=start,
                time_end_bp=end,
                time_mean_bp=None,
                dating_basis="bp_window",
                precision_posture="sample_precise_interval"
                if start is not None
                else "unresolved",
                evidence_class="controlled_numeric_sample_date",
            ),
            source_release="controlled-release",
            provenance_path="original/source.csv",
            provenance_locator=identifier,
        )
        for identifier, start, end in [
            ("young", 100, 110),
            ("also-young", 105, 110),
            ("old", 300, 310),
            ("missing", None, None),
        ]
    )
    locality = replace(
        locality,
        sample_ids=tuple(support.sample_id for support in supports),
        sample_chronologies=supports,
        chronology=replace(
            locality.chronology, time_start_bp=100, time_end_bp=310, time_mean_bp=200
        ),
    )
    return cast(dict[str, Any], serialize_locality_summary(locality))


def _extracted_locality(record: dict[str, Any]) -> ContextPointRecord:
    layer = build_external_point_layer(_collection(record))
    return cast(
        ContextPointRecord,
        extract_context_points(
            [layer], surface=SimpleNamespace(ContextPointRecord=ContextPointRecord)
        )[0],
    )
