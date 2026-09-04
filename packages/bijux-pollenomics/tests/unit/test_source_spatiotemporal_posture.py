from __future__ import annotations

import json
from pathlib import Path
import tempfile

from bijux_pollenomics.data_downloader.source_spatiotemporal_posture import (
    build_source_spatiotemporal_posture_payload,
)


def _rows_by_source(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = payload["rows"]
    assert isinstance(rows, list)
    return {str(row["source_key"]): row for row in rows if isinstance(row, dict)}


def test_posture_registry_refuses_missing_source_authority_without_zero_claims() -> (
    None
):
    with tempfile.TemporaryDirectory() as temporary_directory:
        payload = build_source_spatiotemporal_posture_payload(Path(temporary_directory))

    rows = _rows_by_source(payload)
    assert payload["schema_version"] == "source-spatiotemporal-posture-registry.v2"
    assert rows["raa"]["availability_status"] == "refused"
    assert rows["raa"]["record_count"] is None
    assert rows["raa"]["detail_metrics"] == {
        "all_published_sites": None,
        "fornlamning_count": None,
    }
    assert rows["raa"]["refusal_reasons"] == (
        "missing_raw_inventory",
        "missing_raw_summary",
        "missing_normalized_metadata",
        "missing_density_surface",
        "missing_scientific_review",
    )
    assert rows["svar"]["availability_status"] == "refused"
    assert rows["svar"]["record_count"] is None
    assert rows["svar"]["refusal_reasons"] == ("missing_governing_normalized_registry",)
    assert rows["boundaries"]["availability_status"] == "refused"
    assert rows["boundaries"]["record_count"] is None


def test_posture_registry_distinguishes_empty_svar_registry_from_missing_registry() -> (
    None
):
    with tempfile.TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        registry_path = root / "svar/normalized/sweden_lake_registry.geojson"
        registry_path.parent.mkdir(parents=True)
        registry_path.write_text(
            json.dumps({"type": "FeatureCollection", "features": []}),
            encoding="utf-8",
        )

        rows = _rows_by_source(build_source_spatiotemporal_posture_payload(root))

    assert rows["svar"]["availability_status"] == "available"
    assert rows["svar"]["record_count"] == 0
    assert rows["svar"]["refusal_reasons"] == ()
