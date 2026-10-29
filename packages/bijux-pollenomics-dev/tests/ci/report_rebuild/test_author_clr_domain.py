"""Keep the domain observation from becoming a success or historical repair."""

from __future__ import annotations

import copy
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

MODULE = (
    Path(__file__).parents[3]
    / "src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_clr_domain.py"
)
GUARD = runpy.run_path(str(MODULE))


def publication() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = {"path": "scientific-protocol.json", "sha256": "a" * 64, "bytes": 1}
    objects = [
        {
            "logical_name": name,
            "sha256": str(i) * 64,
            "bytes": i,
            "retention_key": "sha256:" + str(i) * 64,
        }
        for i, name in enumerate(
            ("report.json", "candidate-refusals.json", "selection-freeze.json"), 1
        )
    ]
    authority = {
        "schema_version": "author-love-clr-output-review.v1",
        "approved": True,
        "scientific_saved_products_admitted": True,
        "actual_exit": 0,
        "candidate": "constructed-source",
        "protocol": source,
        "native_status": {
            "native_exit": 0,
            "stage_exit": 0,
            "collector_exit": 0,
            "scientific_main_return": "not_observed_by_unchanged_consumer",
        },
        "summary": dict(
            GUARD["COUNTS"],
            selected_zero_containing_requests=26,
            selected_zero_cells=80,
        ),
        "products": [
            {
                "path": row["logical_name"],
                "sha256": row["sha256"],
                "bytes": row["bytes"],
            }
            for row in objects
        ],
        "original_independent_review": {"sha256": "b" * 64, "bytes": 1},
    }
    report = {
        "schema_version": "author-love-clr-domain-publication.v1",
        "candidate": authority["candidate"],
        "scientific_protocol": source,
        "scientific_acceptance": "not_evaluated",
        "counts": dict(GUARD["COUNTS"]),
        "saved_domain": {
            "zero_containing_requests": 26,
            "zero_cells": 80,
            "geometry_records": 15,
        },
        "selected_outer_dispositions": [
            {
                "outer_target": str(i),
                "baseline": "clr-wgs84-rbf-ridge-v1",
                "status": "refused",
                "selected_method": None,
                "reason_code": "no_eligible_spatial_scale",
                "outer_outcome_decoded": False,
                "outer_score": None,
                "ranking": [
                    {
                        "method": method,
                        "complete_inner_predictions": 0,
                        "mean_inner_total_variation": None,
                    }
                    for method in GUARD["METHODS"]
                ],
            }
            for i in range(15)
        ],
        "original_nominal": {
            "native_exit": 1,
            "native_qualification": "refused_post_scientific_body_origin",
            "original_full_later_import_origins_and_final_return": "not established",
            "separate_saved_product_recovery_native_exit": 0,
            "source_candidate": "70dd58ce28071d3b4ef34af2c800370a52d42bf9",
        },
    }
    index = {
        "schema_version": "author-love-clr-trace-index.v1",
        "objects": objects,
        "all450_candidate_rows_and420_inner_rows_retained": True,
        "raw_payloads_in_product_git": False,
        "independent_output_review": authority["original_independent_review"],
    }
    return report, index, authority


def test_admitted_domain_preserves_all_refusals() -> None:
    report, index, authority = publication()
    evidence = GUARD["validate_products"](report, index, authority)
    assert evidence["maintained_fit_API_attempts"] == 450
    assert evidence["selected_outer_refusals"] == 15
    assert evidence["private_trace_payloads_read"] == 0


@pytest.mark.parametrize(
    "mutation", ["population", "winner", "history", "trace", "native", "main_return"]
)
def test_domain_escalations_are_refused(mutation: str) -> None:
    report, index, authority = copy.deepcopy(publication())
    if mutation == "population":
        report["counts"]["maintained_fit_API_attempts"] = 449
    elif mutation == "winner":
        report["selected_outer_dispositions"][0]["selected_method"] = "clr-ridge-20km"
    elif mutation == "history":
        report["original_nominal"]["native_exit"] = 0
    elif mutation == "trace":
        index["objects"][0] = index["objects"][1]
    elif mutation == "native":
        authority["native_status"]["native_exit"] = 1
    else:
        authority["native_status"]["scientific_main_return"] = 0
    with pytest.raises(ReportRebuildError):
        GUARD["validate_products"](report, index, authority)


def test_unrelated_owner_returns_callback_tuple(tmp_path: Path) -> None:
    assert GUARD["validated_author_clr_domain"](
        tmp_path, {}, [], authority_sha256="0" * 64
    ) == ((), {})
