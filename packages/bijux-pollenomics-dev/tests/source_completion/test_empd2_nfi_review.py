"""Review sheet remains source bound and refuses promoted or duplicate pairs."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.empd2_nfi_review import render_review


def _parents(tmp_path: Path) -> tuple[Path, str, Path, str, Path, str]:
    spatial = tmp_path / "spatial.json"
    spatial.write_text(
        json.dumps(
            {
                "schema_version": "empd2-nfi-spatial-feasibility.v2",
                "scientific_admission": "candidate_only",
            }
        )
    )
    spatial_hash = sha256(spatial.read_bytes()).hexdigest()
    rows = []
    for index in range(16):
        name = f"sample-{index:02d}"
        rows.append(
            {
                "spatial_lead": {
                    "pollen_sample": name,
                    "pair_admission": "candidate_only",
                    "distance_m_wgs84": float(index + 0.123456),
                    "nfi_year": "2013",
                    "pollen_review_reason_codes": ["cross_source_identity_unresolved"]
                    if index == 0
                    else [],
                },
                "source_metadata_excluding_vegdescription": {
                    "samplename": name,
                    "agebp": "NULL" if index == 0 else -63,
                    "ageuncertainty": "A",
                    "samplecontext": "lake",
                    "sampletype": "sediment",
                    "notes": "collected September 2013" if index == 0 else None,
                },
                "publication_link_count": 1 if index == 0 else 0,
                "collection_time_source_note": "collected September 2013"
                if index == 0
                else None,
                "independent_vegetation_pair_admission": False,
            }
        )
    dossier = tmp_path / "dossier.json"
    dossier.write_text(
        json.dumps(
            {
                "schema_version": "empd2-nfi-source-dossier.v1",
                "spatial_report_sha256": spatial_hash,
                "scientific_admission": "candidate_only",
                "independent_vegetation_pair_count": 0,
                "selected_lead_count": 16,
                "samples_with_collection_note_cues": 1,
                "rows": rows,
            }
        )
    )
    guide = tmp_path / "official.pdf"
    guide.write_bytes(b"%PDF-1.7\nfixture")
    return (
        dossier,
        sha256(dossier.read_bytes()).hexdigest(),
        spatial,
        spatial_hash,
        guide,
        sha256(guide.read_bytes()).hexdigest(),
    )


def test_review_keeps_literal_missing_age_and_zero_admission(tmp_path: Path) -> None:
    text = render_review(*_parents(tmp_path))
    assert "0/16 paired references admitted" in text
    assert (
        "sample-00 | NULL | A | lake / sediment | 2013 | 0.12 | 1 | unresolved" in text
    )
    assert "sample-15 | -63 | A | lake / sediment | 2013 | 15.12" in text
    assert "no NFI tree measurements" in text
    assert "Source age is not a collection year" in text
    assert "`sample-00` has the source note “collected September 2013”" in text
    assert "`Nielsen_b4`" not in text


def test_review_refuses_drift_and_identity_promotion(tmp_path: Path) -> None:
    parents = _parents(tmp_path)
    dossier, digest, spatial, spatial_digest, guide, guide_digest = parents
    guide.write_bytes(b"%PDF-1.7\nchanged")
    with pytest.raises(ValueError, match="review_parent_digest_mismatch"):
        render_review(dossier, digest, spatial, spatial_digest, guide, guide_digest)
    guide.write_bytes(b"%PDF-1.7\nfixture")
    report = json.loads(dossier.read_text())
    report["rows"][1]["spatial_lead"]["pollen_sample"] = "sample-00"
    dossier.write_text(json.dumps(report))
    with pytest.raises(ValueError, match="review_sample_identity_mismatch"):
        render_review(
            dossier,
            sha256(dossier.read_bytes()).hexdigest(),
            spatial,
            spatial_digest,
            guide,
            guide_digest,
        )
