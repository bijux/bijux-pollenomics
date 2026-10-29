"""Admit the compact legacy-wrapper domain refusal without private trace access."""

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
    "docs/report/pollen-reconstruction/author-lra-constrained/legacy-wrapper-domain/"
)
OWNER = (
    "pollen-reconstruction/author-lra-constrained/legacy-wrapper-domain/report-products"
)
AUTHORITY = "reports/science/source-cohorts/author-love-legacy-wrapper-domain.json"
PRODUCTS = ("report.json", "trace-index.json")
SOURCE_EPOCH = "af76bcfb287a2997c0102a85a078f3aee3e1f378"
REFUSAL = "unsupported_source_ring_dimensions"
RAW_REVIEW_SHA = "a659a0e1e6a7c9bd706ebfdcfaa86e3f875e24e08206b5d22a8442a0d9fe2f9d"
SUMMARY = {
    "contexts": 225,
    "logical_ancestry": 2715,
    "request_refusals": 39,
    "ring_placeholders_not_executed": 78,
    "sites": 15,
    "source_qualified_API_calls": 39,
    "source_qualified_optimizer_kernel_REVEALS_forward_score_calls": 0,
    "taxa": 30,
    "unique_requests": 39,
}

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

CONFIGURATION = {
    "distance_weighting": "gpm neutral",
    "fall_speed_profile": "disqover-0.9.14-wrapper-v1",
    "max_ring": 2,
    "method": "optimized",
    "optimized_profile": "disqover-0.9.14-source",
    "optimizer_iterations": 300,
    "optimizer_max_evaluations": 16000,
    "optimizer_tolerance": 1e-08,
    "ppe_error": True,
    "repeats": 1,
    "retain_samples": True,
    "seed": 3618983171,
    "stochastic": False,
}

SCIENTIFIC_SOURCES = {
    "reports/science/author-love-analytical-diagnostics/source/inputs.py": {
        "bytes": 9050,
        "sha256": "2f6be1c6719f02dd02a063ff26c5c8d6d1f279a4b7481d1d0ab6084825ea081d",
    },
    "reports/science/legacy-wrapper-diagnostics/protocol.json": {
        "bytes": 29049,
        "sha256": "d2f46647351b239981d848823cb1f12e334b85e98fde6865fce9f4d834d18f15",
    },
    "reports/science/legacy-wrapper-diagnostics/source/replay.py": {
        "bytes": 12211,
        "sha256": "de090a4fc034a26d395ff8b536b05a76043ed4592a7bd6cc6d75717b69b35c39",
    },
}

ORIGINAL_PRODUCTS = {
    "dispositions.json": {
        "bytes": 107700,
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/legacy-wrapper-diagnostic-execution/native/products/dispositions.json",
        "sha256": "80ff245d577892b436c5d68f85b2d37e3f9b6cfe7bc33c0466c35ba2ecaeee9b",
    },
    "report.json": {
        "bytes": 1217,
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/legacy-wrapper-diagnostic-execution/native/products/report.json",
        "sha256": "60b7fa6189eb3b228e3a3f8b8c12d40eba63d89e6d0e7a27cd75c129955d70c9",
    },
}

ORIGINAL_NOMINAL = {
    "full_original_import_origin_admission": False,
    "native_exit": 1,
    "original_final_return_observed": False,
    "saved_product_recovery_native_exit": 0,
    "source_epoch": "70dd58ce28071d3b4ef34af2c800370a52d42bf9",
    "training_protocol_sha256": "7953aec717a0bf440eca6d26e5c4d9bca03e3d783a005ab311f09d3d9b4db4dd",
}

REASON_DETAIL = (
    "DISQOVER 0.9.14 drops ring-matrix dimensions for evaluated single-local or nonzero "
    "single-regional rings with multiple taxa; this source-compatible profile refuses those "
    "requests"
)

DISPOSITIONS_SHA = "204a535f87066207aa5069d43fd145b659c23e48afefe1e2cbe6ad19277f4168"

PINS = {
    "docs/report/pollen-reconstruction/author-lra-constrained/legacy-wrapper-domain/report.json": {
        "bytes": 52607,
        "sha256": "508b0d253b113983f93fe0c8ad015c16a2569a5a5ffed54d6cb65aa802897fe5",
    },
    "docs/report/pollen-reconstruction/author-lra-constrained/legacy-wrapper-domain/trace-index.json": {
        "bytes": 909,
        "sha256": "c11ec4282c2c941db0362dde5ec1841d9479a3096b9e1ff89cebd7d953853a8a",
    },
    "reports/science/author-love-analytical-diagnostics/source/inputs.py": {
        "bytes": 9050,
        "sha256": "2f6be1c6719f02dd02a063ff26c5c8d6d1f279a4b7481d1d0ab6084825ea081d",
    },
    "reports/science/legacy-wrapper-diagnostics/protocol.json": {
        "bytes": 29049,
        "sha256": "d2f46647351b239981d848823cb1f12e334b85e98fde6865fce9f4d834d18f15",
    },
    "reports/science/legacy-wrapper-diagnostics/source/replay.py": {
        "bytes": 12211,
        "sha256": "de090a4fc034a26d395ff8b536b05a76043ed4592a7bd6cc6d75717b69b35c39",
    },
    "reports/science/source-cohorts/author-love-legacy-wrapper-domain.json": {
        "bytes": 3300,
        "sha256": "00e610cc4dabdf6b45a713c2abe3ed91acf789b5767d845a8b7a41a957395416",
    },
}


ORIGINAL_PLAN = {
    "bytes": 916332,
    "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/legacy-wrapper-diagnostic-execution/plan.json",
    "sha256": "37a5b2b9b4303197f6826d43ae8220e25e7dce6f5b3ceaa9f4962cddf3c665ea",
}
NATIVE_TERMINAL = {
    "bytes": 2275,
    "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/legacy-wrapper-diagnostic-execution/native/terminal.json",
    "sha256": "a6e11b51e211ac06f759cbdbf002465772c8f5f7174e9251595f8c9c42b38bb1",
}


def require(condition: bool, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not condition:
        raise ReportRebuildError("Legacy wrapper domain: " + reason)


def validate_products(
    report: dict[str, Any], index: dict[str, Any], authority: dict[str, Any]
) -> JsonObject:
    """Check saved products against pinned source and scientific contracts."""
    require(
        authority["schema_version"] == "legacy-wrapper-domain-publication-authority.v1"
        and authority["approved"] is True
        and type(authority["actual_exit"]) is int
        and authority["actual_exit"] == 0
        and authority["scientific_saved_products_admitted"] is True
        and authority["source_epoch"] == report["source_epoch"] == SOURCE_EPOCH
        and authority["original_plan"] == ORIGINAL_PLAN
        and authority["native_terminal"] == NATIVE_TERMINAL
        and authority["independent_output_review"]["sha256"] == RAW_REVIEW_SHA,
        "exact admitted source epoch and independent refusal authority required",
    )
    require(
        report["schema_version"] == "legacy-wrapper-domain-publication.v1"
        and report["summary"] == authority["summary"] == SUMMARY
        and all(type(report["summary"][k]) is int for k in SUMMARY),
        "complete39refusal/78nonexecuted denominator required",
    )
    require(
        tuple(report["taxa"]) == TAXA
        and report["configuration"] == CONFIGURATION
        and report["scientific_sources"] == SCIENTIFIC_SOURCES,
        "exact labelled taxon/configuration/source handoff required",
    )
    require(
        report["original_products"]
        == authority["original_products"]
        == ORIGINAL_PRODUCTS,
        "original native product identities differ",
    )
    rows = report["request_dispositions"]
    require(
        len(rows)
        == len({r["nominal_request_sha256"] for r in rows})
        == len({r["legacy_request_sha256"] for r in rows})
        == 39,
        "complete distinct39 request correspondence required",
    )
    require(
        hashlib.sha256(
            json.dumps(
                rows, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode()
        ).hexdigest()
        == authority["request_dispositions_sha256"]
        == DISPOSITIONS_SHA,
        "exact original-to-legacy identities and raw handoff required",
    )
    for row in rows:
        require(
            row["status"] == "refused"
            and row["reason_code"] == REFUSAL
            and row["legacy_request_sha256"] != row["nominal_request_sha256"]
            and type(row["local_seed"]) is int
            and row["local_seed"] == 3618983171
            and row["ring_dispositions"]
            == [
                {"ring_index": 0, "status": "not_returned_request_refused"},
                {"ring_index": 1, "status": "not_returned_request_refused"},
            ],
            "typed request refusal and nonexecuted ring placeholders required",
        )
        values = row["raw_regional_cover"]
        require(
            len(values) == 30
            and all(
                type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1
                for v in values
            )
            and abs(math.fsum(values) - 1) <= 30 * 0.000005 + 1e-12,
            "unchanged source-rounded regional fractions required",
        )
        require(
            row["basins"]["regional_basin_type"] == "lake"
            and all(
                type(row["basins"][k]) in (int, float) and row["basins"][k] > 0
                for k in ("regional_basin_diameter_m", "local_basin_diameter_m")
            ),
            "declared source basin geometry required",
        )
    require(
        report["reason_detail"] == REASON_DETAIL
        and report["zero_downstream_calls_qualification"]
        == "Source-derived from exact pinned early guard, not instrumented call counters."
        and report["original_nominal"] == ORIGINAL_NOMINAL
        and all(
            report[k] is False
            for k in (
                "scientific_main_return_observed",
                "full_run_lra_cached_execution",
                "predictions_scores_or_selection_admitted",
            )
        )
        and authority["scientific_main_return_observed"] is False,
        "refusal/source-qualified counts/original native1/recovery0 limits required",
    )
    roles = {
        "legacy-request-dispositions": ORIGINAL_PRODUCTS["dispositions.json"],
        "legacy-native-report": ORIGINAL_PRODUCTS["report.json"],
        "legacy-native-terminal": authority["native_terminal"],
    }
    require(
        index
        == {
            "schema_version": "legacy-wrapper-domain-trace-index.v1",
            "objects": [
                {
                    "sha256": r["sha256"],
                    "bytes": r["bytes"],
                    "retention_key": "sha256:" + r["sha256"],
                    "roles": [role],
                }
                for role, r in sorted(roles.items())
            ],
        },
        "exact three private trace identities required",
    )
    for name in PRODUCTS:
        require(
            authority["public_products"][name] == PINS[PREFIX + name],
            "acyclic authority must bind both current public products",
        )
    return {
        "requests": 39,
        "request_refusals": 39,
        "ring_placeholders_not_executed": 78,
        "private_trace_payloads_read": 0,
        "models_or_scores_executed": 0,
    }


def validated_author_legacy_wrapper_domain(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate retained wrapper-domain evidence and original refusals."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared:
        return (), {}
    require(
        len(declared) == 1
        and declared[0].get("role") == "retained_source"
        and declared[0].get("paths") == sorted(PREFIX + name for name in PRODUCTS),
        "one exact two-product retained owner required",
    )
    bodies = {}
    for name, expected in PINS.items():
        path = _regular_confined_file(repository, name, "legacy wrapper domain")
        require(
            path.stat().st_nlink == 1 and path.stat().st_size == expected["bytes"],
            "physical product/source alias or size differs",
        )
        raw = path.read_bytes()
        require(
            hashlib.sha256(raw).hexdigest() == expected["sha256"],
            "frozen source/product bytes differ",
        )
        bodies[name] = raw
    entries = []
    for name in PRODUCTS:
        entry = tracked_by_path.get(PREFIX + name)
        require(
            entry is not None
            and entry.sha256 == PINS[PREFIX + name]["sha256"]
            and entry.size == PINS[PREFIX + name]["bytes"],
            "current product inventory differs",
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
