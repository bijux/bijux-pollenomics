"""Standalone sample exports preserve owned source chronology and identities."""

from __future__ import annotations

import csv
from dataclasses import replace
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.adna.domain.models import AdnaSampleRecord
from bijux_pollenomics.reporting.rendering import record_exports

from ...adna.domain.test_adna_temporal_query import _sample_with_interval


def _source_sample(younger: int | None, older: int | None) -> AdnaSampleRecord:
    sample = _sample_with_interval(younger, older)
    return replace(
        sample,
        identity=replace(sample.identity, stable_token="owned:Ångström"),
        master_id="native-master-17",
        archive_native_sample_id="ERS-source-9",
        archive_native_experiment_id="ERX-source-3",
        paper_native_sample_label="Paper sample α",
        supplementary_table_sample_label="Table S2 row 17",
        source_native_identity_kind="biological_sample",
        sample_lineage_path="original/source.xlsx",
        sample_lineage_locator="Sheet2!row17",
        sample_lineage_excerpt="Ångström | native-master-17",
        chronology=replace(
            sample.chronology,
            original_text="Source date α",
            source_mean_bp_text=" 100.00 ",
            date_stddev_bp="2.50",
            dating_basis="source-stated method",
            evidence_class="source-stated class",
            precision_posture="source-stated precision",
            refusal_reason_code="source_age_system_not_comparable",
        ),
        chronology_strength="source-strength",
        chronology_normalization_status="retained_refusal",
        chronology_provenance_path="original/source.xlsx",
        chronology_provenance_kind="source_table_row",
        chronology_provenance_locator="Sheet2!row17",
        chronology_provenance_text="Source date α\nuncertainty not a confidence bound",
        chronology_conflict_note="Original alternative remains unresolved",
    )


@pytest.mark.parametrize("bounds", [(None, None), (0, 0), (-1, 10), (200, 100)])
def test_default_sample_exports_preserve_source_metadata_and_native_identity(
    tmp_path: Path, bounds: tuple[int | None, int | None]
) -> None:
    sample = _source_sample(*bounds)
    payload = record_exports.serialize_sample_record(sample)
    assert payload["schema_version"] == "adna-sample-record-export.v2"
    support = cast(dict[str, object], payload["sample_chronology"])
    assert support["sample_id"] == sample.genetic_id != sample.master_id
    assert support["chronology"] == sample.chronology.as_dict()
    assert support["source_release"] == sample.source_release
    assert support["provenance_path"] == sample.chronology_provenance_path
    assert support["provenance_locator"] == sample.chronology_provenance_locator
    assert support["provenance_excerpt"] == sample.chronology_provenance_text
    assert support["provenance_kind"] == sample.chronology_provenance_kind
    assert support["chronology_strength"] == sample.chronology_strength
    assert support["normalization_status"] == sample.chronology_normalization_status
    assert support["conflict_note"] == sample.chronology_conflict_note
    for key in ("reference_epoch", "age_type", "calibration_status", "model"):
        assert support[key] == "not_separately_declared"
    identity = cast(dict[str, object], payload["sample_identity"])
    assert identity["archive_native_sample_id"] == "ERS-source-9"
    assert identity["archive_native_experiment_id"] == "ERX-source-3"
    assert identity["paper_native_sample_label"] == "Paper sample α"
    assert identity["supplementary_table_sample_label"] == "Table S2 row 17"
    assert identity["master_id"] == "native-master-17"
    assert identity["stable_token"] == "owned:Ångström"
    assert identity["sample_lineage_excerpt"] == sample.sample_lineage_excerpt
    assert json.loads(json.dumps(payload)) == payload

    csv_path = tmp_path / "samples.csv"
    record_exports.write_samples_csv(csv_path, (sample,))
    with csv_path.open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 1
    assert tuple(rows[0]) == record_exports.SAMPLE_EXPORT_FIELDS
    assert json.loads(rows[0]["sample_chronology"]) == support
    assert json.loads(rows[0]["sample_identity"]) == identity
    assert rows[0]["schema_version"] == payload["schema_version"]
    assert rows[0]["time_start_bp"] == ("" if bounds[0] is None else str(bounds[0]))
    assert rows[0]["time_end_bp"] == ("" if bounds[1] is None else str(bounds[1]))

    geojson_path = tmp_path / "samples.geojson"
    record_exports.write_samples_geojson(geojson_path, (sample,))
    collection = json.loads(geojson_path.read_bytes())
    assert collection["schema_version"] == "adna-sample-geojson-collection.v2"
    feature = collection["features"][0]
    assert feature["schema_version"] == "adna-sample-geojson.v2"
    assert feature["properties"] == payload


def test_named_period_missing_time_survives_without_numeric_conversion() -> None:
    sample = _source_sample(None, None)
    sample = replace(
        sample,
        chronology=replace(
            sample.chronology,
            original_text="Bronze Age",
            dating_basis="named_period",
            date_stddev_bp="",
        ),
    )
    payload = record_exports.serialize_sample_record(sample)
    support = cast(dict[str, object], payload["sample_chronology"])
    assert payload["time_start_bp"] is None and payload["time_end_bp"] is None
    assert support["chronology"] == sample.chronology.as_dict()


def test_explicit_legacy_schema_keeps_previous_fields_without_claiming_losslessness(
    tmp_path: Path,
) -> None:
    sample = _source_sample(None, None)
    current = record_exports.serialize_sample_record(sample)
    legacy = record_exports.serialize_sample_record(
        sample, schema_version="adna-sample-record-export.v1"
    )
    assert tuple(legacy) == record_exports.LEGACY_SAMPLE_EXPORT_FIELDS
    assert legacy == {
        **{key: current[key] for key in legacy if key != "schema_version"},
        "schema_version": "adna-sample-record-export.v1",
    }
    output = tmp_path / "legacy.csv"
    record_exports.write_samples_csv(
        output, (sample,), schema_version="adna-sample-record-export.v1"
    )
    with output.open(newline="") as stream:
        row = next(csv.DictReader(stream))
    assert tuple(row) == record_exports.LEGACY_SAMPLE_EXPORT_FIELDS
    assert row["schema_version"] == "adna-sample-record-export.v1"
    collection = record_exports.build_samples_geojson(
        (sample,), schema_version="adna-sample-geojson-collection.v1"
    )
    feature = cast(list[dict[str, object]], collection["features"])[0]
    assert feature["schema_version"] == "adna-sample-geojson.v1"
    assert feature["properties"] == legacy


@pytest.mark.parametrize("version", ["", "adna-sample-record-export.v3", "v2"])
def test_unknown_sample_export_version_refuses_before_writing(
    tmp_path: Path, version: str
) -> None:
    target = tmp_path / "unsupported.csv"
    with pytest.raises(ValueError, match="Unsupported sample export schema"):
        record_exports.write_samples_csv(target, (), schema_version=version)
    assert not target.exists()


@pytest.mark.parametrize(
    "version", ["adna-sample-geojson-collection.v3", "adna-sample-geojson.v1"]
)
def test_unknown_collection_version_refuses_without_creating_output(
    tmp_path: Path, version: str
) -> None:
    target = tmp_path / "unsupported.geojson"
    with pytest.raises(ValueError, match="Unsupported sample GeoJSON collection"):
        record_exports.write_samples_geojson(target, (), schema_version=version)
    assert not target.exists()
