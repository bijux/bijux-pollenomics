"""Admit a nonselectable circular-receiver diagnostic without private trace access."""

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

AUTHORITY = "reports/science/source-cohorts/author-love-circular-receiver-domain.json"

AUTHORITY_IDENTITIES: dict[str, Any] = {
    "collector": {
        "bytes": 1094,
        "path": "artifacts/science/circular-receiver-diagnostic-execution/collected-execution.json",
        "sha256": "064ac82994e79c7e545bc283f82172d57157095fb2ff47bf09b01acee8a55827",
    },
    "native_terminal": {
        "bytes": 2580,
        "path": "artifacts/science/circular-receiver-diagnostic-execution/native/terminal.json",
        "sha256": "c9a37100bea72e49b8f2ab4a9b816bd1ab9c2340e679936deed7b8dd3a7e359a",
    },
    "observation": {
        "bytes": 4012,
        "path": "artifacts/science/circular-receiver-output-admission/observation.json",
        "sha256": "f0a859dd91cca3c69c0c4905f956ba4bb6a80c893c84625f871d3ef2ba22fbb6",
    },
    "observer_execution": {
        "bytes": 2294,
        "path": "artifacts/science/circular-receiver-output-admission/execution.json",
        "sha256": "ea97b623f4cfd45c1b5a9c2d00643c3e67ba90ce71b7244d9c5d26c5132541ff",
    },
    "observer_source_review": {
        "bytes": 5559,
        "path": "artifacts/science/circular-receiver-output-admission/source-review.json",
        "sha256": "40e1c017f43da29a82c7404d721c36ac10d3bed4a1be8aea49e28601f6dfb62d",
    },
    "original_products": {
        "prediction-dispositions.json": {
            "bytes": 4793984,
            "path": "artifacts/science/circular-receiver-diagnostic-execution/native/products/prediction-dispositions.json",
            "sha256": "7a289c9e4bb8d4c51ec40e37a34a7c26b3a4865419f3d7f1eb3b1d77b26591ee",
        },
        "receiver-responses.json": {
            "bytes": 151258,
            "path": "artifacts/science/circular-receiver-diagnostic-execution/native/products/receiver-responses.json",
            "sha256": "1ea90c59301d553914f5d2f4679f9ad6f0deab73efb4fbe9c27c5be6a95bf2f4",
        },
        "report.json": {
            "bytes": 2316,
            "path": "artifacts/science/circular-receiver-diagnostic-execution/native/products/report.json",
            "sha256": "b9eaa0d6e53284f4dae7afb28f44355698dbc7eb17f9ce88cd416151941f21ab",
        },
        "trials.jsonl": {
            "bytes": 3887100,
            "path": "artifacts/science/circular-receiver-diagnostic-execution/native/products/trials.jsonl",
            "sha256": "50f439318170badc1ecca450565edd5942a030862c49a8eed542933836041cf4",
        },
    },
    "plan": {
        "bytes": 918254,
        "path": "artifacts/science/circular-receiver-diagnostic-execution/plan.json",
        "sha256": "122ae29178bfa2fee7363078826a5e6963a3c9ede1f653527c48a2fbc81c016d",
    },
}

LIMITS = {
    "calibrated_uncertainty_admitted": False,
    "comparison": "Forward-to-forward difference only; original point inverse and conditional disk "
    "forward are unmatched. Source calK2inner and actual annulus support also differ.",
    "independently_recomputed_kernel_values": False,
    "isolated_basin_effect_admitted": False,
    "matched_inverse_qualified": False,
    "population": "Previously exposed TW5 development; source-declared 1250–1750 calibrated-BP "
    "support. Reference epoch, calibration model and age uncertainty unqualified.",
    "quadrature_error": "Nonrigorous adaptive quadrature estimates, not guaranteed probability bounds "
    "or ecological uncertainty.",
    "scientific_acceptance": "not_evaluated",
    "scientific_main_return_observed": False,
    "selection_eligible": False,
    "target_accuracy_admitted": False,
}

OWNER = "pollen-reconstruction/author-lra-constrained/circular-receiver-domain/report-products"

PINS = {
    "docs/report/pollen-reconstruction/author-lra-constrained/circular-receiver-domain/report.json": {
        "bytes": 1330913,
        "sha256": "60028a7eb11e87e04107b5ce94061e2704722418995a19431f6a5a8eafc8bf1d",
    },
    "docs/report/pollen-reconstruction/author-lra-constrained/circular-receiver-domain/trace-index.json": {
        "bytes": 1175,
        "sha256": "7057d29aa1df2cd50ca5a75d7cb409c321c654ac32f5ed2a7121f5fcf6590c11",
    },
    "reports/science/circular-receiver-development/protocol.json": {
        "bytes": 30503,
        "sha256": "2125396402ba4a57157c4a06987d717e52abd44d1a40ab0b8bb76b538301c03c",
    },
    "reports/science/circular-receiver-development/source/inputs.py": {
        "bytes": 15437,
        "sha256": "c3e61501679e55203ed79ba4850f0a36eb950689d164d604dca798815a7fe0b1",
    },
    "reports/science/circular-receiver-development/source/receiver.py": {
        "bytes": 11491,
        "sha256": "2f5d04112a71006744b25c933f56f494d22f5c334a93252164d6a08d23d40f43",
    },
    "reports/science/circular-receiver-development/source/replay.py": {
        "bytes": 10162,
        "sha256": "43a1d5c52a24219fcf96ab813d59aca44f149687ef67b3f1f51d7c0959cf24d2",
    },
    "reports/science/source-cohorts/author-love-circular-receiver-domain.json": {
        "bytes": 6716,
        "sha256": "e1e78ad42f334419af145822582b629a6e5ed7663d06f3d14de1ae643a50f2ea",
    },
}

PREFIX = (
    "docs/report/pollen-reconstruction/author-lra-constrained/circular-receiver-domain/"
)

PROJECTION_DIGESTS = {
    "contexts": "aa5c19ff327bc886edc0098a95d61290d999d6d45d235b50aadbda9c2fdc8793",
    "dispositions": "3a059efd8c0e165c17afc45382cf88c37159efd6885e72a0b77e9aacca169d8a",
    "native_runtime": "ce9404ecdb29cfeef4802339f021c95a4b2b0e5bd13aec0d60e3a74a6d5b9203",
    "nominal_authority": "f0bf07bf7f5aa21d1898cb23f468d28ba9a58f9be9dfbb9becf4ba9f0c9341bf",
    "observer_calls": "6fbd703b1bb0337cc91936084be4492b388a6006981c0ef1e42a8524eb7a12e4",
    "observer_summary": "270a05b7fc47cfb0c5dfc879ab7d9561de59f353c5fcc728708bd3bd00e7fd24",
    "original_nominal": "682e533d1b5af1fe8fe1bfb9f7536fa9236b73125d83de3aabd3cce6f0b53c79",
    "original_products": "acb9f593440c17f8c7a7026d820e672c511660914731c9dcb83c71d675f01a97",
    "parameters": "d16163471b8e2de02110e4ca1654e969f41f58d9befc83fdf8c2a1c612216502",
    "response_tables": "0433ffe5c93d583133466e575b375f39e9d496e15ba8a4d1f192f08c01058459",
    "scientific_limits": "334533f106d8485021c74fad4e97171defe3655f0b569cf82fda25a2fd2cefb7",
    "scientific_sources": "6d4666fc8ec109cdb93f204985e4a9c747200d2803986f3c21fc34b8e86987bb",
    "setting": "5c2c3c84c433bfb8814fd56bd754732292c5d5d30e3181485512d83a9e1e83f2",
    "taxa": "6223215ed7ffa800f190abdbff4eda970ca914ded46cced21e2a60345ba0afac",
}

SCIENTIFIC_SOURCES = {
    "reports/science/circular-receiver-development/protocol.json": {
        "bytes": 30503,
        "sha256": "2125396402ba4a57157c4a06987d717e52abd44d1a40ab0b8bb76b538301c03c",
    },
    "reports/science/circular-receiver-development/source/inputs.py": {
        "bytes": 15437,
        "sha256": "c3e61501679e55203ed79ba4850f0a36eb950689d164d604dca798815a7fe0b1",
    },
    "reports/science/circular-receiver-development/source/receiver.py": {
        "bytes": 11491,
        "sha256": "2f5d04112a71006744b25c933f56f494d22f5c334a93252164d6a08d23d40f43",
    },
    "reports/science/circular-receiver-development/source/replay.py": {
        "bytes": 10162,
        "sha256": "43a1d5c52a24219fcf96ab813d59aca44f149687ef67b3f1f51d7c0959cf24d2",
    },
}

SOURCE_EPOCH = "97e95bee8da4f59459b4d6fa5b118a4a0750b196"

SUMMARY = {
    "contexts": 225,
    "diagnostic_slots": 675,
    "forward_calls": 675,
    "independent_arithmetic": "Decimal50 deposition/background/normalization and forward-to-forward "
    "TV from recorded K, not kernel recomputation or observational "
    "accuracy.",
    "independently_recomputed_kernel_values": False,
    "inner_slots": 630,
    "kernel_calls": 1800,
    "maximum_absolute_pollen_decimal_error": "2.3290742513414647534736544053000620E-16",
    "new_spatial_fits": 0,
    "optimizer_attempts": 0,
    "outer_slots": 45,
    "predicted_diagnostic": 675,
    "refusal_reasons": {},
    "refused": 0,
    "response_tables": 15,
    "score_calls": 0,
    "sites": 15,
    "taxa": 30,
    "unique_fit_requests_reused": 39,
}

PRODUCTS = ("report.json", "trace-index.json")
BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")


def require(condition: bool, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not condition:
        raise ReportRebuildError("Circular receiver: " + reason)


def digest(value: Any) -> str:
    """Return the exact retained-source byte digest."""
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def validate_products(
    report: dict[str, Any], index: dict[str, Any], authority: dict[str, Any]
) -> JsonObject:
    """Check saved products against pinned source and scientific contracts."""
    require(
        authority["schema_version"]
        == "circular-receiver-domain-publication-authority.v1"
        and authority["approved"] is True
        and authority["scientific_saved_products_admitted"] is True
        and type(authority["actual_exit"]) is int
        and authority["actual_exit"] == 0
        and report["source_epoch"] == authority["source_epoch"] == SOURCE_EPOCH,
        "actual saved-product authority and original scientific epoch required",
    )
    require(
        all(
            authority[key] == expected for key, expected in AUTHORITY_IDENTITIES.items()
        )
        and report["original_products"] == AUTHORITY_IDENTITIES["original_products"],
        "exact native, observer, source-review and four raw trace identities required",
    )
    require(
        report["schema_version"] == "circular-receiver-domain-publication.v1"
        and digest(report["observer_summary"]) == digest(SUMMARY)
        and digest(authority["observer_summary"]) == digest(SUMMARY)
        and report["scientific_limits"] == authority["scientific_limits"] == LIMITS
        and report["scientific_sources"]
        == authority["scientific_sources"]
        == SCIENTIFIC_SOURCES,
        "source-qualified arithmetic and nonselectable mismatched-forward scope required",
    )
    for key, expected in PROJECTION_DIGESTS.items():
        require(
            digest(report[key]) == authority["projection_digests"][key] == expected,
            "complete admitted " + key + " projection differs",
        )
    require(
        len(report["taxa"])
        == len(set(report["taxa"]))
        == len(report["parameters"])
        == 30
        and tuple(row["taxon"] for row in report["parameters"])
        == tuple(report["taxa"]),
        "labelled30 PPE, SD and settling-speed rows required",
    )
    tables = report["response_tables"]
    require(len(tables) == 15, "all15 receiver geometries required")
    for target, table in tables.items():
        require(
            table["target"] == target
            and table["status"] == "evaluated"
            and table["matched_inverse_qualified"] is False
            and table["profile"] == "conditional-isotropic-gpm-disk-annulus"
            and table["kernel_calls"] == 120
            and len(table["ring_bounds_m"])
            == len(table["full_k"])
            == len(table["estimated_absolute_error"])
            == 4
            and table["ring_bounds_m"][0][0] == table["receiver_radius_m"],
            "complete source-qualified disk response required",
        )
        for values in table["full_k"] + table["estimated_absolute_error"]:
            require(
                len(values) == 30
                and all(
                    type(v) in (int, float) and math.isfinite(v) and v >= 0
                    for v in values
                ),
                "finite labelled response/error vectors required",
            )
    contexts = report["contexts"]
    require(len(contexts) == 225, "all225 outer/inner ancestry contexts required")
    for key, row in contexts.items():
        require(
            key == digest(row)
            and row["target"] in tables
            and row["outer_target"] in tables,
            "context identity or geometry differs",
        )
        require(
            len(row["source_request_sha256s"]) in (12, 13)
            and len(set(row["source_request_sha256s"]))
            == len(row["source_request_sha256s"]),
            "unique training-request lineage required",
        )
    slots = report["dispositions"]
    require(len(slots) == 675, "all675 diagnostic dispositions required")
    identities = {(row["context_sha256"], row["baseline"]) for row in slots}
    require(
        identities == {(key, baseline) for key in contexts for baseline in BASELINES}
        and len(identities) == len(slots),
        "exact three baseline slots per context required",
    )
    for row in slots:
        context = contexts[row["context_sha256"]]
        require(
            all(row[key] == context[key] for key in ("kind", "outer_target", "target")),
            "paired context differs",
        )
        require(
            row["status"] == "predicted_diagnostic"
            and row["selection_eligible"] is False
            and row["matched_inverse_qualified"] is False
            and row["scientific_acceptance"] == "not_evaluated",
            "diagnostic cannot become selection or accuracy",
        )
        value = row["prediction_difference_total_variation"]
        require(
            type(value) in (int, float)
            and math.isfinite(value)
            and 0 <= value <= 1
            and row["forward_calls"] == 1,
            "finite forward-to-forward difference required",
        )
    roles = AUTHORITY_IDENTITIES["original_products"]
    require(
        index
        == {
            "schema_version": "circular-receiver-domain-trace-index.v1",
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
        "exact four external scientific traces required",
    )
    require(
        all(
            authority["public_products"][name] == PINS[PREFIX + name]
            for name in PRODUCTS
        ),
        "acyclic public-product bindings differ",
    )
    return {
        "response_tables": 15,
        "diagnostic_slots": 675,
        "predicted_diagnostic": 675,
        "refused": 0,
        "outer_slots": 45,
        "inner_slots": 630,
        "source_kernel_calls": 1800,
        "source_forward_calls": 675,
        "private_trace_payloads_read": 0,
        "models_or_scores_executed": 0,
        "selection_eligible": False,
    }


def validated_circular_receiver_domain(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate retained circular-receiver diagnostics and declared domain."""
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
        path = _regular_confined_file(repository, name, "circular receiver")
        require(
            path.stat().st_nlink == 1 and path.stat().st_size == expected["bytes"],
            "physical product/source alias or size differs",
        )
        raw = path.read_bytes()
        require(
            hashlib.sha256(raw).hexdigest() == expected["sha256"],
            "frozen product or computational source differs",
        )
        bodies[name] = raw
    entries = []
    for name in PRODUCTS:
        entry = tracked_by_path.get(PREFIX + name)
        require(
            entry is not None
            and entry.sha256 == PINS[PREFIX + name]["sha256"]
            and entry.size == PINS[PREFIX + name]["bytes"],
            "current tracked product differs",
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
