"""Keep native identity/raw rows private and refuse unsupported chronology claims."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.archaeology.native_lead_support.report import (
    aggregate,
)
from bijux_pollenomics_dev.source_completion.archaeology.native_lead_support.streams import (
    NativeWitness,
    WitnessBudget,
)


def private_fixture(root: Path) -> Path:
    root.mkdir()
    files: dict[str, object] = {}
    rows: dict[str, dict[str, object]] = {
        "geometry": {
            "role": "native_remains_geometry",
            "native_uuid": "private-native-id",
        },
        "support": {
            "lead_id": "toy-lead",
            "native_uuid": "private-native-id",
            "role": "native_remains_geometry",
            "support": [
                {"radius_metres": 10000, "status": "point_within_projected_circle"}
            ],
        },
        "native-owners": {
            "native_uuid": "private-native-id",
            "families": {
                "egenskap": {
                    "rows": [
                        {
                            "typ": {"sqlite_type": "text", "value": "Typ"},
                            "varde": {
                                "sqlite_type": "text",
                                "value": "private-native-period-text",
                            },
                        }
                    ]
                }
            },
        },
    }
    for name, row in rows.items():
        writer = NativeWitness(root / (name + ".ndjson.gz"), WitnessBudget(10000), 5000)
        writer.write(row)
        files[name + ".ndjson.gz"] = writer.close()
    source = {
        "sha256": "96bbe197a84c70b64f047873ded15ce5df568198dc0794870a782decb82fed0b",
        "bytes": 2291224576,
        "recorded_capture": "2026-09-13",
    }
    report: dict[str, object] = {
        "source": source,
        "chronology_intervals": None,
        "chronology_admission": False,
        "scientific_admission": False,
        "output_files": files,
        "leads": [],
        "unique_geometry_occurrences": 1,
        "unique_native_uuids": 1,
        "support_links": 1,
        "native_field_storage_type_counts": {},
        "native_owner_lookup_status_counts": {},
        "decoded_witness_bytes": 1,
    }
    (root / "report.json").write_text(json.dumps(report))
    return root


def test_public_projection_contains_only_aggregate_native_id_counts(
    tmp_path: Path,
) -> None:
    report = aggregate(private_fixture(tmp_path / "private"))
    encoded = json.dumps(report)
    assert "private-native-id" not in encoded
    assert "private-native-period-text" not in encoded
    assert report["chronology_intervals"] is None
    assert report["eligible_archaeological_event_count"] == 0
    assert report["field_permission"] is False
    assert report["scientific_admission"] is False
    assert report["historical_density_equivalence"] is False


@pytest.mark.parametrize(
    "field,value",
    [
        ("chronology_intervals", {}),
        ("chronology_admission", True),
        ("scientific_admission", True),
    ],
)
def test_public_aggregate_refuses_unsupported_interval_or_admission(
    tmp_path: Path, field: str, value: object
) -> None:
    private = private_fixture(tmp_path / "private")
    report = json.loads((private / "report.json").read_bytes())
    report[field] = value
    (private / "report.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="cannot admit"):
        aggregate(private)


def test_changed_private_native_stream_cannot_be_relabelled_as_source_proof(
    tmp_path: Path,
) -> None:
    private = private_fixture(tmp_path / "private")
    (private / "geometry.ndjson.gz").write_bytes(b"foreign bytes")
    with pytest.raises(ValueError, match="byte identity differs"):
        aggregate(private)
