from __future__ import annotations

import json
from pathlib import Path
import tempfile

from bijux_pollenomics.data_downloader.source_spatiotemporal_posture import (
    build_source_spatiotemporal_posture_payload,
)

REPO_ROOT = Path(__file__).resolve().parents[4]


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


def test_repository_posture_uses_governed_landclim_counts_and_refuses_missing_authority() -> (
    None
):
    first = build_source_spatiotemporal_posture_payload(REPO_ROOT / "data")
    second = build_source_spatiotemporal_posture_payload(REPO_ROOT / "data")
    rows = _rows_by_source(first)

    assert first == second
    assert rows["landclim"]["record_count"] == 490
    assert rows["landclim"]["numeric_interval_record_count"] == 480
    assert rows["landclim"]["detail_metrics"] == {
        "site_sequence_record_count": 490,
        "numeric_interval_record_count": 480,
        "grid_cell_count": 77,
        "temporal_grid_feature_count": 2515,
    }
    assert rows["raa"]["availability_status"] == "refused"
    assert rows["raa"]["record_count"] is None
    assert rows["raa"]["numeric_interval_record_count"] == 0
    assert rows["raa"]["detail_metrics"] == {
        "all_published_sites": None,
        "fornlamning_count": None,
    }
    assert rows["svar"]["availability_status"] == "refused"
    assert rows["svar"]["record_count"] is None
    assert rows["svar"]["numeric_interval_record_count"] == 0
    assert rows["svar"]["detail_metrics"] == {"lake_count": None}


def test_public_source_indexes_do_not_promote_refused_or_stale_counts() -> None:
    docs = {
        relative_path: (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in (
            "docs/public/pollenomics/index.md",
            "docs/public/pollenomics-data/overview/index.md",
            "docs/public/pollenomics-data/overview/cross-domain-evidence-matrix.md",
            "docs/public/pollenomics-data/evidence/temporal-semantics.md",
            "docs/public/pollenomics-data/sources/landclim.md",
            "docs/public/pollenomics-data/sources/raa.md",
            "docs/public/pollenomics-data/sources/source-family-matrix.md",
            "docs/public/pollenomics-data/sources/svar.md",
            "docs/public/pollenomics-data/publications/landclim-exports.md",
            "docs/public/pollenomics-data/publications/map-inputs.md",
            "docs/public/pollenomics-data/publications/maps.md",
            "docs/public/pollenomics-data/publications/publication-types.md",
            "docs/public/pollenomics-data/publications/raa-exports.md",
        )
    }

    combined = "\n".join(docs.values())
    assert "492 LandClim" not in combined
    assert "2,809 dataset-cell-window" not in combined
    assert "across 88 aggregate cells" not in combined
    assert "RAÄ density source representing 761,917" not in combined
    assert "and 40,565 SVAR lakes" not in combined
    assert "761,917" not in combined
    assert "318,265" not in combined
    assert "416,913" not in combined
    assert "40,565" not in combined
    assert "27,450" not in combined
    assert "490 LandClim site sequences" in combined
    assert "2,515 dataset-cell-window features across 77 aggregate cells" in combined
    assert "RAÄ authority is refused" in combined
    assert "SVAR authority is refused" in combined
