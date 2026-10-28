"""Actual public serializers retain source eligibility through external and map readers."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.reporting.bundles.atlas_bundle.context import (
    extract_context_points,
)
from bijux_pollenomics.reporting.context import build_external_point_layer
from bijux_pollenomics.reporting.map_document.adna_exports import (
    locality_export_records,
)
from bijux_pollenomics.reporting.map_document.temporal_admission import (
    feature_temporal_admission,
)

from .support import (
    _browser,
    _collection,
    _extracted_locality,
    _owned_locality_record,
    _record,
)


@pytest.mark.parametrize("wrapped", [False, True])
@pytest.mark.parametrize("political", ["Sweden", "Denmark", None])
def test_locality_native_identity_and_geography_survive_all_reader_projections(
    wrapped: bool, political: str | None
) -> None:
    record = _owned_locality_record()
    record["political_entity"] = political
    record["locality_identity"]["political_entity"] = political
    identity = deepcopy(record["locality_identity"])
    if wrapped:
        record["identity"] = record.pop("locality_identity")
        del record["political_entity"]
        record = locality_export_records(
            {"schema_version": record.pop("schema_version"), "localities": [record]}
        )[0]
    assert feature_temporal_admission(record)[0] == "admitted"
    assert _browser([record])[0]["status"] == "valid"
    layer = build_external_point_layer(_collection(record))
    mapped = cast(list[dict[str, Any]], layer["features"])[0]
    assert mapped["country"] == (political or "")
    key = "identity" if wrapped else "locality_identity"
    assert mapped[key] == identity
    assert mapped["source_record"][key] == identity
    point = _extracted_locality(record)
    assert point.country == (political or "")
    assert point.source_record is not None and point.source_record[key] == identity


@pytest.mark.parametrize(
    "change", ["geography", "token", "namespace", "anchors", "object", "dual"]
)
def test_conflicting_or_malformed_locality_native_identity_never_admits(
    change: str,
) -> None:
    record = _owned_locality_record()
    if change == "geography":
        record["political_entity"] = "conflicting declared geography"
    elif change == "token":
        record["locality_token"] = "conflicting token"
    elif change == "namespace":
        record["locality_namespace"] = "conflicting namespace"
    elif change == "anchors":
        record["locality_identity"]["source_anchor_tokens"] = [False]
    elif change == "object":
        record["locality_identity"] = []
    else:
        record["identity"] = {
            **record["locality_identity"],
            "stable_token": "conflicting token",
        }
    assert feature_temporal_admission(record) == ("refused", None)
    assert _browser([record])[0]["status"] == "refused"
    with pytest.raises(ValueError):
        build_external_point_layer(_collection(record))


def test_locality_csv_has_explicit_json_native_identity(tmp_path: Path) -> None:
    import csv

    from bijux_pollenomics.reporting.rendering.record_exports import (
        write_localities_csv,
    )

    from ....analysis.fieldwork.ranking_examples import _locality

    locality = _locality("Native locality", 59, 18)
    output = tmp_path / "localities.csv"
    write_localities_csv(output, [locality])
    with output.open(newline="") as handle:
        row = next(csv.DictReader(handle))
    assert json.loads(row["locality_identity"]) == locality.identity.as_dict()
    assert row["political_entity"] == (locality.identity.political_entity or "")


def test_locality_csv_nullable_geography_is_retained_without_inferred_null() -> None:
    record = _owned_locality_record()
    record["political_entity"] = ""
    record["locality_identity"]["political_entity"] = None
    assert feature_temporal_admission(record)[0] == "admitted"
    assert _browser([record])[0]["status"] == "valid"
    mapped = cast(
        list[dict[str, Any]],
        build_external_point_layer(_collection(record))["features"],
    )[0]
    assert mapped["country"] == ""
    assert mapped["source_record"]["political_entity"] == ""
    assert mapped["locality_identity"]["political_entity"] is None


@pytest.mark.parametrize("kind", ["sample", "locality"])
def test_colocated_same_name_exports_keep_distinct_native_operational_identity(
    kind: str,
) -> None:
    records = (
        [_record(), _record()]
        if kind == "sample"
        else [_owned_locality_record(), _owned_locality_record()]
    )
    pairs = [("a:b", "c"), ("a", "b:c")]
    for record, (namespace, token) in zip(records, pairs, strict=True):
        record["locality"] = "Same displayed locality"
        if kind == "sample":
            record["genetic_id"] = token
            record["sample_namespace"] = namespace
            record["sample_identity"].update(namespace=namespace, stable_token=token)
            record["sample_chronology"]["sample_id"] = token
        else:
            record["locality_identity"].update(namespace=namespace, stable_token=token)
    points = [_extracted_locality(record) for record in records]
    assert [json.loads(point.record_id) for point in points] == [
        list(pair) for pair in pairs
    ]
    assert len({point.record_id for point in points}) == 2
    assert {point.name for point in points} == {"Same displayed locality"}
    assert [
        point.source_record["locality"] for point in points if point.source_record
    ] == ["Same displayed locality"] * 2
    from bijux_pollenomics.analysis.fieldwork.evidence_richness.temporal import (
        _attach_temporal_context,
    )

    from ....analysis.fieldwork.lake_fieldwork_preparation.support import _candidate

    candidate = _candidate(
        lake_name="Controlled",
        lake_label="Controlled",
        latitude=59,
        longitude=18,
        ambiguity_flags=(),
        direct_pollen_source_count=0,
    )
    summaries = _attach_temporal_context(
        [candidate],
        pollen_points=points,
        human_points=(),
        animal_points=(),
        sead_points=(),
    )[0].temporal_context_points
    assert summaries
    assert all(len(summary.representative_source_records) == 2 for summary in summaries)


def test_generic_context_keeps_existing_title_identity_and_missing_locality_native_id_is_not_invented() -> (
    None
):
    generic = {"name": "Generic display", "record_id": "source-row"}
    mapped = build_external_point_layer(_collection(generic))
    point = extract_context_points(
        [mapped], surface=SimpleNamespace(ContextPointRecord=ContextPointRecord)
    )[0]
    assert point.record_id == "Generic display"
    legacy = _owned_locality_record()
    del legacy["locality_identity"]
    mapped = build_external_point_layer(_collection(legacy))
    raw = cast(list[dict[str, Any]], mapped["features"])[0]
    assert raw["evidence_row_id"] == ""


def test_actual_locality_csv_null_geography_reaches_typed_context_without_restoration(
    tmp_path: Path,
) -> None:
    import csv

    from bijux_pollenomics.reporting.rendering.record_exports import (
        write_localities_csv,
    )

    from ....analysis.fieldwork.ranking_examples import _locality

    locality = _locality("Native nullable geography", 59, 18, sample_count=2)
    locality = replace(
        locality, identity=replace(locality.identity, political_entity=None)
    )
    output = tmp_path / "native-locality.csv"
    write_localities_csv(output, [locality])
    with output.open(newline="") as handle:
        record: dict[str, Any] = dict(next(csv.DictReader(handle)))
    for key in ("sample_chronologies", "locality_identity"):
        record[key] = json.loads(record[key])
    for key in ("sample_count", "time_start_bp", "time_end_bp", "time_mean_bp"):
        record[key] = int(record[key]) if record[key] else None
    record["sample_ids"] = (
        record["sample_ids"].split(";") if record["sample_ids"] else []
    )
    assert record["political_entity"] == ""
    assert record["locality_identity"]["political_entity"] is None
    assert feature_temporal_admission(record)[0] == "admitted"
    assert _browser([record])[0]["status"] == "valid"
    point = _extracted_locality(record)
    assert point.country == ""
    assert point.source_record is not None
    assert point.source_record["political_entity"] == ""
    retained_identity = point.source_record["locality_identity"]
    assert isinstance(retained_identity, dict)
    assert retained_identity["political_entity"] is None
    assert point.occurrence_supports is not None
    assert [row.support_id for row in point.occurrence_supports] == list(
        locality.sample_ids
    )
