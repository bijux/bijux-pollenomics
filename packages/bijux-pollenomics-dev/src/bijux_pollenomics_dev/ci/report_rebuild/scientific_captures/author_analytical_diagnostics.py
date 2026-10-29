"""Admit compact negative analytical LOVE diagnostics without private trace access."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.ownership import _regular_confined_file

PREFIX = (
    "docs/report/pollen-reconstruction/author-lra-constrained/analytical-diagnostics/"
)
OWNER = "pollen-reconstruction/author-lra-constrained/analytical-diagnostics/report-products"
AUTHORITY = "reports/science/source-cohorts/author-love-analytical-diagnostics.json"
PRODUCTS = ("report.json", "trace-index.json")
SOURCE_CANDIDATE = "23ea4670d12ee6f61e0fb086c20f6dfe455eb0e4"
TAXA = (
    "Abies.alba",
    "Alnus.glutinosa",
    "Amanranthaceae.Chenopodiaceae",
    "Artemisia",
    "Betula",
    "Buxus.sempervirens",
    "Calluna.vulgaris",
    "Carpinus.betulus",
    "Carpinus.orientalis",
    "Castanea",
    "Cerealia.t",
    "Corylus.avellana",
    "Cyperaceae",
    "Ericaceae",
    "Fagus.sylvatica",
    "Fraxinus",
    "Juniperus",
    "Phillyrea",
    "Picea",
    "Pinus",
    "Pistacia",
    "Plantago.lanceolata.type",
    "Poaceae",
    "Quercus.deciduous",
    "Quercus.evergreen",
    "Rumex.acetosa.t",
    "Salix",
    "Secale",
    "Tilia",
    "Ulmus",
)
SCIENTIFIC_SOURCES = {
    "reports/science/author-love-analytical-diagnostics/source/inputs.py": {
        "sha256": "2f6be1c6719f02dd02a063ff26c5c8d6d1f279a4b7481d1d0ab6084825ea081d",
        "bytes": 9050,
    },
    "reports/science/author-love-analytical-diagnostics/source/replay.py": {
        "sha256": "b6b7578092bfacb4ec4a0b4fed8081446b8fb47328f52350a79801ae50b42f0b",
        "bytes": 12656,
    },
    "reports/science/author-love-analytical-diagnostics/protocol.json": {
        "sha256": "17a56327cab995eb3f44b3c2fd03a68d0de31261c87d13d0a236bf3d5ba55b89",
        "bytes": 28142,
    },
    "reports/science/author-love-analytical-diagnostics/source-locations.json": {
        "sha256": "fa72d7eea24d9c5ab06f25bb21de374577852c41c4613617dbe59ecfd7463dc8",
        "bytes": 1792,
    },
}
PINS = {
    "docs/report/pollen-reconstruction/author-lra-constrained/analytical-diagnostics/report.json": {
        "sha256": "6c174ccf083ce86557c6c9dd196f5e0b7d245ad419cef0b7dea5f0ac5d977315",
        "bytes": 56592,
    },
    "docs/report/pollen-reconstruction/author-lra-constrained/analytical-diagnostics/trace-index.json": {
        "sha256": "d905dd1753420eb64b07456b8711771f77fe0803fc25e4fef9ac3b882d5d61a4",
        "bytes": 917,
    },
    "reports/science/author-love-analytical-diagnostics/source/inputs.py": {
        "sha256": "2f6be1c6719f02dd02a063ff26c5c8d6d1f279a4b7481d1d0ab6084825ea081d",
        "bytes": 9050,
    },
    "reports/science/author-love-analytical-diagnostics/source/replay.py": {
        "sha256": "b6b7578092bfacb4ec4a0b4fed8081446b8fb47328f52350a79801ae50b42f0b",
        "bytes": 12656,
    },
    "reports/science/author-love-analytical-diagnostics/protocol.json": {
        "sha256": "17a56327cab995eb3f44b3c2fd03a68d0de31261c87d13d0a236bf3d5ba55b89",
        "bytes": 28142,
    },
    "reports/science/author-love-analytical-diagnostics/source-locations.json": {
        "sha256": "fa72d7eea24d9c5ab06f25bb21de374577852c41c4613617dbe59ecfd7463dc8",
        "bytes": 1792,
    },
    "reports/science/source-cohorts/author-love-analytical-diagnostics.json": {
        "sha256": "5157bea6f7682f193ab9f4834c40f062f96d516a2880a1626256142fe89bd5d5",
        "bytes": 19251,
    },
}


def require(condition: bool, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not condition:
        raise ReportRebuildError("Saved analytical diagnostics: " + reason)


def validate_products(
    report: dict[str, Any], index: dict[str, Any], authority: dict[str, Any]
) -> JsonObject:
    """Check saved products against pinned source and scientific contracts."""
    require(
        authority["schema_version"] == "author-love-analytical-cohort-output-review.v1"
        and authority["approved"] is True
        and type(authority["actual_exit"]) is int
        and authority["actual_exit"] == 0
        and authority["scientific_saved_products_admitted"] is True
        and authority["analytical_composition_prediction_admitted"] is False,
        "independent negative-diagnostic admission required",
    )
    require(
        report["schema_version"] == "author-love-analytical-publication.v1"
        and report["source_candidate"]
        == authority["candidate"]
        == authority["source_epoch"]
        == SOURCE_CANDIDATE
        and report["protocol_sha256"] == authority["scientific_protocol"]["sha256"],
        "source epoch or protocol differs",
    )
    summary = report["summary"]
    require(
        all(
            type(summary[key]) is int
            for key in (
                "unique_pairs",
                "returned_requests",
                "analytical_LOVE_calls",
                "refused_requests",
                "raw_closed_composition_rings",
                "nonfinite_taxon_cells",
                "new_REVEALS_optimizer_forward_score_calls",
                "ring_dispositions",
                "geometry_supported_rings",
                "rings_with_negative_taxa",
                "negative_taxon_cells",
                "above_one_taxon_cells",
                "rings_with_above_one_taxa",
                "labelled_scalar_equation_comparisons",
            )
        ),
        "integer outcome populations required",
    )
    require(
        summary == authority["summary"]
        and summary["unique_pairs"]
        == summary["returned_requests"]
        == summary["analytical_LOVE_calls"]
        == 39
        and summary["refused_requests"]
        == summary["raw_closed_composition_rings"]
        == summary["nonfinite_taxon_cells"]
        == summary["new_REVEALS_optimizer_forward_score_calls"]
        == 0
        and summary["ring_dispositions"]
        == summary["geometry_supported_rings"]
        == summary["rings_with_negative_taxa"]
        == 78
        and summary["negative_taxon_cells"] == 605
        and summary["above_one_taxon_cells"] == 29
        and summary["rings_with_above_one_taxa"] == 25
        and summary["ring_status_counts"] == {"invalid_composition": 78}
        and summary["labelled_scalar_equation_comparisons"] == 2340,
        "all39request/78rawnegative ring denominators required",
    )
    require(
        tuple(report["taxa"]) == TAXA
        and len(TAXA) == 30
        and len(set(TAXA)) == 30
        and summary["sites"] == 15
        and summary["taxa"] == 30
        and summary["contexts"] == 225
        and summary["logical_ancestry"] == 2715
        and summary["temporal_support"]
        == {
            "bins": [{"bin_id": "author-TW5", "older_bp": 1750, "younger_bp": 1250}],
            "decision_evidence_id": "decision",
            "rule": "declared_bin_stationarity",
        },
        "matched taxa/site/calendar-BP/source-support scope required",
    )
    joins = report["request_joins"]
    require(
        joins == authority["request_correspondence"]
        and len(joins)
        == len({r["nominal_request_sha256"] for r in joins})
        == len({r["analytical_request_sha256"] for r in joins})
        == 39
        and all(
            r["nominal_request_sha256"] != r["analytical_request_sha256"]
            and r["raw_ring_statuses"] == ["invalid_composition", "invalid_composition"]
            for r in joins
        ),
        "complete distinct current analytical request joins required",
    )
    expected = {
        (r["nominal_request_sha256"], r["analytical_request_sha256"], i)
        for r in joins
        for i in range(2)
    }
    rows = report["ring_dispositions"]
    require(
        len(rows)
        == len(
            {
                (
                    r["nominal_request_sha256"],
                    r["analytical_request_sha256"],
                    r["ring_index"],
                )
                for r in rows
            }
        )
        == 78
        and {
            (
                r["nominal_request_sha256"],
                r["analytical_request_sha256"],
                r["ring_index"],
            )
            for r in rows
        }
        == expected,
        "every unique request/ring disposition required",
    )
    require(
        all(
            type(r["ring_index"]) is int
            and r["geometry_supported"] is True
            and r["status"] == "invalid_composition"
            and type(r["negative_taxon_count"]) is int
            and 0 < r["negative_taxon_count"] <= 30
            and type(r["above_one_taxon_count"]) is int
            and 0 <= r["above_one_taxon_count"] <= 30
            and all(
                type(r[k]) in (int, float) and math.isfinite(r[k])
                for k in ("raw_minimum", "raw_maximum", "raw_sum")
            )
            and r["raw_minimum"] < 0
            and (r["raw_maximum"] > 1) is (r["above_one_taxon_count"] > 0)
            and abs(r["raw_sum"] - 1) <= 1e-9
            for r in rows
        ),
        "retain raw finite negative and above-one estimates without closure repair",
    )
    require(
        sum(r["negative_taxon_count"] for r in rows) == 605
        and sum(r["above_one_taxon_count"] for r in rows) == 29
        and sum(r["above_one_taxon_count"] > 0 for r in rows) == 25
        and min(r["raw_minimum"] for r in rows) == summary["raw_cover_minimum"]
        and max(r["raw_maximum"] for r in rows) == summary["raw_cover_maximum"],
        "exact raw extrema and taxon populations required",
    )
    require(
        report["scientific_source_refs"] == SCIENTIFIC_SOURCES
        and report["original_reference"] == authority["products"]["report.json"]
        and report["raw_diagnostics_reference"]
        == authority["products"]["analytical-diagnostics.json"],
        "public source and original native product references differ",
    )
    require(
        report["direct_analytical_API_calls"] == 39
        and all(
            report[k] is False
            for k in (
                "full_run_lra_cached_request_execution",
                "prediction_compositions_admitted",
                "scores_or_method_choice_executed",
                "old31taxon_result_reused",
            )
        )
        and report["original_nominal"]
        == {
            "source_candidate": "70dd58ce28071d3b4ef34af2c800370a52d42bf9",
            "training_protocol_sha256": "7953aec717a0bf440eca6d26e5c4d9bca03e3d783a005ab311f09d3d9b4db4dd",
            "native_exit": 1,
            "saved_product_recovery_native_exit": 0,
            "full_original_import_origin_admission": "not established",
            "original_post_report_final_return": "not established",
        },
        "direct diagnostic and original nominal native1/separate recovery0 scope required",
    )
    roles = {
        "analytical-raw-diagnostics": authority["products"][
            "analytical-diagnostics.json"
        ],
        "analytical-native-report": authority["products"]["report.json"],
        "analytical-native-terminal": authority["native_terminal"],
    }
    require(
        index
        == {
            "schema_version": "author-love-analytical-trace-index.v1",
            "objects": [
                {
                    "sha256": row["sha256"],
                    "bytes": row["bytes"],
                    "retention_key": "sha256:" + row["sha256"],
                    "roles": [role],
                }
                for role, row in sorted(roles.items())
            ],
        },
        "exact three retained raw diagnostic/report/terminal identities required",
    )
    return {
        "requests": 39,
        "raw_ring_dispositions": 78,
        "invalid_raw_compositions": 78,
        "closed_compositions": 0,
        "negative_taxon_cells": 605,
        "above_one_taxon_cells": 29,
        "private_trace_payloads_read": 0,
        "models_or_scores_executed": 0,
    }


def validated_author_analytical_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate retained analytical author evidence and its declared scope."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared:
        return (), {}
    paths = declared[0].get("paths")
    require(
        len(declared) == 1
        and declared[0].get("role") == "retained_source"
        and isinstance(paths, list)
        and all(isinstance(name, str) for name in paths)
        and len(paths) == 2
        and set(paths) == {PREFIX + name for name in PRODUCTS},
        "one exact two-product retained owner required",
    )
    bodies = {}
    for name, expected in PINS.items():
        path = _regular_confined_file(repository, name, "analytical diagnostics")
        require(
            path.stat().st_nlink == 1 and path.stat().st_size == expected["bytes"],
            "physical source/product size or alias differs",
        )
        raw = path.read_bytes()
        require(
            hashlib.sha256(raw).hexdigest() == expected["sha256"],
            "frozen public source/product bytes differ",
        )
        bodies[name] = raw
    entries = []
    for name in PRODUCTS:
        entry = tracked_by_path.get(PREFIX + name)
        require(
            entry is not None
            and entry.sha256 == PINS[PREFIX + name]["sha256"]
            and entry.size == PINS[PREFIX + name]["bytes"],
            "current compact product inventory differs",
        )
        assert entry is not None
        entries.append(entry)
    evidence = validate_products(
        json.loads(bodies[PREFIX + "report.json"]),
        json.loads(bodies[PREFIX + "trace-index.json"]),
        json.loads(bodies[AUTHORITY]),
    )
    evidence["authority_sha256"] = PINS[AUTHORITY]["sha256"]
    return tuple(entries), evidence
