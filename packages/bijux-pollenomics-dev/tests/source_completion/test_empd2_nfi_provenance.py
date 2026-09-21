"""Source citations and age codes remain distinct from an admitted pairing."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3

import pytest

from bijux_pollenomics_dev.source_completion.empd2_nfi_provenance import (
    source_dossier,
)


def _fixture(tmp_path: Path) -> tuple[Path, str, Path, str]:
    source = tmp_path / "empd.sqlite3"
    db = sqlite3.connect(source)
    db.execute(
        "CREATE TABLE metadata (samplename TEXT, originalsamplename TEXT, "
        "sitename TEXT, country TEXT, longitude REAL, latitude REAL, "
        "locationreliability TEXT, locationnotes TEXT, areaofsite REAL, "
        "samplecontext TEXT, sampletype TEXT, samplemethod TEXT, agebp, "
        "ageuncertainty TEXT, notes TEXT, empd_version TEXT, vegdescription TEXT)"
    )
    db.execute(
        "CREATE TABLE ageuncertainties (ageuncertainty TEXT, age TEXT, description TEXT)"
    )
    db.execute("CREATE TABLE metapubli (samplename TEXT, publiid INTEGER)")
    db.execute("CREATE TABLE publications (publiid INTEGER, doi TEXT, reference TEXT)")
    db.executemany(
        "INSERT INTO metadata VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                "lead",
                "original-lead",
                "site-1",
                "Sweden",
                18.0,
                60.0,
                "A",
                "source-location-note",
                None,
                "moss",
                "surface",
                "sample method",
                -63,
                "A",
                "Surface sample collected September 2013",
                "2",
                "secret vegetation label",
            ),
            (
                "distant",
                "original-distant",
                "site-2",
                "Sweden",
                19.0,
                61.0,
                "B",
                None,
                None,
                "soil",
                "surface",
                "method",
                "NULL",
                "B",
                None,
                "2",
                "second secret label",
            ),
        ],
    )
    db.execute(
        "INSERT INTO ageuncertainties VALUES ('A','0BP to Present','Modern sample')"
    )
    db.execute("INSERT INTO metapubli VALUES ('lead',7)")
    db.execute("INSERT INTO publications VALUES (7,'10.1234/example','Source paper')")
    db.commit()
    db.close()
    source_hash = sha256(source.read_bytes()).hexdigest()
    spatial = tmp_path / "spatial.json"
    spatial.write_text(
        json.dumps(
            {
                "schema_version": "empd2-nfi-spatial-feasibility.v2",
                "scientific_admission": "candidate_only",
                "source_hashes": {"empd2_source": source_hash},
                "swedish_pollen_samples": 2,
                "thresholds_descriptive_only": {"1000": {"pollen_samples": 1}},
                "nearest_nfi_row_by_pollen_sample": [
                    {
                        "pollen_sample": "lead",
                        "distance_m_wgs84": 500.0,
                        "pollen_agebp_source_native": -63,
                        "pollen_ageuncertainty_source_native": "A",
                    },
                    {
                        "pollen_sample": "distant",
                        "distance_m_wgs84": 1500.0,
                        "pollen_agebp_source_native": "NULL",
                        "pollen_ageuncertainty_source_native": "B",
                    },
                ],
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return source, source_hash, spatial, sha256(spatial.read_bytes()).hexdigest()


def test_dossier_preserves_source_age_and_citation_without_labels(
    tmp_path: Path,
) -> None:
    result = source_dossier(*_fixture(tmp_path))
    assert result["selected_lead_count"] == 1
    assert result["samples_with_publication_links"] == 1
    assert result["samples_with_collection_note_cues"] == 1
    assert result["source_age_uncertainty_counts"] == {"A": 1}
    assert result["source_explicit_collection_date_column"] is None
    row = result["rows"][0]
    assert row["source_metadata_excluding_vegdescription"]["agebp"] == -63
    assert row["source_age_uncertainty_lookup"] == {
        "source_age_range_label": "0BP to Present",
        "source_description": "Modern sample",
    }
    assert row["source_publications"] == [
        {"publiid": 7, "doi": "10.1234/example", "reference": "Source paper"}
    ]
    assert row["collection_time_source_note"] == (
        "Surface sample collected September 2013"
    )
    assert row["collection_time_status"] == "source_note_requires_review"
    assert "secret vegetation label" not in json.dumps(result)
    assert result["independent_vegetation_pair_count"] == 0


def test_source_or_report_drift_refuses_dossier(tmp_path: Path) -> None:
    source, source_hash, spatial, spatial_hash = _fixture(tmp_path)
    with pytest.raises(ValueError, match="source_digest_mismatch"):
        source_dossier(source, "0" * 64, spatial, spatial_hash)
    spatial.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="spatial_report_digest_mismatch"):
        source_dossier(source, source_hash, spatial, spatial_hash)


def test_new_collection_date_column_requires_timing_review(tmp_path: Path) -> None:
    source, _, spatial, _ = _fixture(tmp_path)
    db = sqlite3.connect(source)
    db.execute("ALTER TABLE metadata ADD COLUMN collection_year INTEGER")
    db.commit()
    db.close()
    source_hash = sha256(source.read_bytes()).hexdigest()
    report = json.loads(spatial.read_text(encoding="utf-8"))
    report["source_hashes"]["empd2_source"] = source_hash
    spatial.write_text(json.dumps(report, sort_keys=True), encoding="utf-8")
    with pytest.raises(ValueError, match="metadata_schema_requires_timing_review"):
        source_dossier(
            source, source_hash, spatial, sha256(spatial.read_bytes()).hexdigest()
        )
