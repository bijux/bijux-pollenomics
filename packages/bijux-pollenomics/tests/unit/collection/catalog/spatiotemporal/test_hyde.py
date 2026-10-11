"""The shared posture registry exposes pending HYDE without accepting file claims."""

from pathlib import Path

from bijux_pollenomics.collection.catalog.spatiotemporal import (
    build_source_spatiotemporal_posture_payload,
)


def test_pending_hyde_posture_preserves_unavailable_geography(tmp_path: Path) -> None:
    bogus = tmp_path / "hyde/3.5/normalized/manifest.json"
    bogus.parent.mkdir(parents=True)
    bogus.write_text('{"schema_version":"hyde.v1","cell_count":9999}')
    payload = build_source_spatiotemporal_posture_payload(tmp_path)
    rows = payload["rows"]
    assert isinstance(rows, list)
    row = next(row for row in rows if row["source_key"] == "hyde")
    assert row["availability_status"] == "refused"
    assert row["record_count"] is None
    assert row["numeric_interval_record_count"] == 0
    assert row["detail_metrics"] == {
        "native_cell_count": None,
        "admitted_country_count": None,
    }
    assert row["temporal_support_posture"] == "refused_unverified_source"
    assert row["capability_and_materialization_are_independent"] is True
