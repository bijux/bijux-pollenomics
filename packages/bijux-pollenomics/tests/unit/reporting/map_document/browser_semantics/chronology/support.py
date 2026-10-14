"""Exact source-member fixture shared by browser chronology transports."""

from __future__ import annotations


def _feature() -> dict[str, object]:
    return {
        "chronology_role": "locality_sample_coverage_hull",
        "sample_ids": ["young", "old", "missing"],
        "time_start_bp": 100,
        "time_end_bp": 310,
        "sample_chronologies": [
            {
                "schema_version": "adna-sample-chronology-support.v1",
                "sample_id": sample_id,
                "chronology": {
                    "original_text": "original source",
                    "time_start_bp": younger,
                    "time_end_bp": older,
                    "time_mean_bp": None,
                    "precision_posture": "sample_precise_interval"
                    if younger is not None and older is not None
                    else "unresolved",
                    "evidence_class": "controlled_numeric_sample_date",
                },
            }
            for sample_id, younger, older in [
                ("young", 100, 110),
                ("old", 300, 310),
                ("missing", None, None),
            ]
        ],
    }
