"""Admit the compact seeded search budget refusals without private trace access."""

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
    "docs/report/pollen-reconstruction/author-lra-constrained/seeded-search-domain/"
)

OWNER = (
    "pollen-reconstruction/author-lra-constrained/seeded-search-domain/report-products"
)

AUTHORITY = "reports/science/source-cohorts/author-love-seeded-search-domain.json"

PRODUCTS = ("report.json", "trace-index.json")

SOURCE_EPOCH = "96f064592b47380172c3c5276b442ac35a9ad16f"

SUMMARY = {
    "accepted_rings": 0,
    "contexts": 225,
    "kernels_independently_recomputed": False,
    "ledger_events": 156,
    "logical_ancestry": 2715,
    "maximum_objective_absolute_difference": 1.7763568394002505e-15,
    "new_model_optimizer_kernel_forward_score_calls": 0,
    "not_attempted_rings": 0,
    "objective_arithmetic_precision": 50,
    "objective_certification_calls": 78,
    "optimizer_attempts": 78,
    "refused_rings": 78,
    "requests": 39,
    "ring_dispositions": 78,
    "search_evaluations_recorded": 1248000,
}

NATIVE_CALLS = {
    "LOVEoptim_calls": 39,
    "REVEALS_calls": 0,
    "forward_calls": 0,
    "objective_certification_calls": 78,
    "optimizer_attempts": 78,
    "score_calls": 0,
    "search_evaluations": 1248000,
}

SETTING = {
    "bounds": "unit_box",
    "id": "ring-preserving-differential-evolution",
    "max_search_evaluations": 16000,
    "maxiter": 300,
    "polish": False,
    "popsize": 10,
    "root_seed": 7,
    "seed_mapping": "canonical LRA SeedSequence(root_seed).spawn(2)[1] local child; one "
    "generator per request, shared across rings",
    "tolerance": 1e-08,
    "updating": "immediate",
    "workers": 1,
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

SCIENTIFIC_SOURCES = {
    "reports/science/seeded-love-development/protocol.json": {
        "bytes": 29520,
        "sha256": "595f5371c90fdf370434c3f522645e9ad79631f330cd673f37ecafac4f774917",
    },
    "reports/science/seeded-love-development/source/inputs.py": {
        "bytes": 8927,
        "sha256": "8c2bcc03e89a1ac1c35fcd3dc29b7277a03f72112aa605f16bd97723bb0cd7ae",
    },
    "reports/science/seeded-love-development/source/replay.py": {
        "bytes": 9560,
        "sha256": "dc26ca0574e199e97fbe86bf9011d62986f0054b36414f41a9be286f3f18fbf3",
    },
    "reports/science/seeded-love-development/source/search.py": {
        "bytes": 9233,
        "sha256": "b2e4526d8fbb4bbf8d29b093976ffabb38a618aa7b3e6a2971454915a31c7a71",
    },
}

ORIGINAL_PRODUCTS = {
    "report.json": {
        "bytes": 2352,
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/seeded-love-diagnostic-execution/native/products/report.json",
        "sha256": "086bd37d927063079a431398020644e68b950645ac0bab3550c48340157412be",
    },
    "seeded-diagnostics.json": {
        "bytes": 509712,
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/seeded-love-diagnostic-execution/native/products/seeded-diagnostics.json",
        "sha256": "b786b3ce27d43717495b4b7e8c428366b71638cd3f0eb68156da0615408b32d9",
    },
    "trials.jsonl": {
        "bytes": 251545,
        "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/seeded-love-diagnostic-execution/native/products/trials.jsonl",
        "sha256": "73825eaefedb312af6f738612ffb4324eb2b1bf1db6afb2bfbb98d9756783e59",
    },
}

ORIGINAL_NOMINAL = {
    "full_original_import_origin_admission": False,
    "native_exit": 1,
    "original_final_return_observed": False,
    "saved_product_recovery_native_exit": 0,
    "source_epoch": "70dd58ce28071d3b4ef34af2c800370a52d42bf9",
}

COUNTER_QUALIFICATION = (
    "The observer new_model_optimizer_kernel_forward_score_calls:0 describes independent "
    "saved-output reading only. Native search attempted78rings; recorded kernels are "
    "source-qualified, not independently recomputed."
)

ORIGINAL_PLAN = {
    "bytes": 916802,
    "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/seeded-love-diagnostic-execution/plan.json",
    "sha256": "8a5668cdba14cd1ac012c4aa03baf79cf6de625f331e7f3fcbff24474f480bd8",
}

NATIVE_TERMINAL = {
    "bytes": 2538,
    "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/seeded-love-diagnostic-execution/native/terminal.json",
    "sha256": "578665d82036d13d571ac71c19097b972787e6048753c2b005a9c14205bdb40e",
}

OBSERVATION = {
    "bytes": 2657,
    "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/seeded-love-output-admission/observation.json",
    "sha256": "089882e6cd5423f0dc84aa98525f8e7975e653f8cf29a2fbface9a942ac65caf",
}

OBSERVATION_EXECUTION = {
    "bytes": 1614,
    "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/seeded-love-output-admission/execution.json",
    "sha256": "1c2a1016ec0f5b36bab25b7f4a1e2cfba9c9ab4d2ff6fe9951189c8c314fd495",
}

REQUESTS_SHA = "9059dd81809c1095913bde2a7367de9d56e0a9f29d735a5ffd9616b27c632271"

RINGS_SHA = "6451744abd2b8ed4f9a78efca37e1d72fa666026a51cab09a0abc5253401ecfc"

PARAMETERS_SHA = "d16163471b8e2de02110e4ca1654e969f41f58d9befc83fdf8c2a1c612216502"

PINS = {
    "docs/report/pollen-reconstruction/author-lra-constrained/seeded-search-domain/report.json": {
        "bytes": 144839,
        "sha256": "a085d8ea5854da50a4eb58f6ade3794948b3a746d2caacd056f1441dc927a286",
    },
    "docs/report/pollen-reconstruction/author-lra-constrained/seeded-search-domain/trace-index.json": {
        "bytes": 1174,
        "sha256": "27a3b91dec09315ad7040bcd542551533561919b8ff6eb9eb3661385416e81be",
    },
    "reports/science/seeded-love-development/protocol.json": {
        "bytes": 29520,
        "sha256": "595f5371c90fdf370434c3f522645e9ad79631f330cd673f37ecafac4f774917",
    },
    "reports/science/seeded-love-development/source/inputs.py": {
        "bytes": 8927,
        "sha256": "8c2bcc03e89a1ac1c35fcd3dc29b7277a03f72112aa605f16bd97723bb0cd7ae",
    },
    "reports/science/seeded-love-development/source/replay.py": {
        "bytes": 9560,
        "sha256": "dc26ca0574e199e97fbe86bf9011d62986f0054b36414f41a9be286f3f18fbf3",
    },
    "reports/science/seeded-love-development/source/search.py": {
        "bytes": 9233,
        "sha256": "b2e4526d8fbb4bbf8d29b093976ffabb38a618aa7b3e6a2971454915a31c7a71",
    },
    "reports/science/source-cohorts/author-love-seeded-search-domain.json": {
        "bytes": 3549,
        "sha256": "0cca5cfc7113a6ccf86ac2ab95ddc584ce808e36516759f6567f900f73e52888",
    },
}


def require(condition: bool, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not condition:
        raise ReportRebuildError("Seeded LOVE search: " + reason)


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
        authority["schema_version"] == "seeded-love-domain-publication-authority.v1"
        and authority["approved"] is True
        and type(authority["actual_exit"]) is int
        and authority["actual_exit"] == 0
        and authority["scientific_saved_products_admitted"] is True
        and authority["source_epoch"] == report["source_epoch"] == SOURCE_EPOCH
        and authority["original_plan"] == ORIGINAL_PLAN
        and authority["native_terminal"] == NATIVE_TERMINAL
        and authority["observation"] == OBSERVATION
        and authority["observation_execution"] == OBSERVATION_EXECUTION
        and authority["observation_has_aggregate_actual_exit"] is False
        and type(authority["observation_execution_actual_exit"]) is int
        and authority["observation_execution_actual_exit"] == 0,
        "actual native and separate observer execution authority required",
    )
    require(
        report["schema_version"] == "seeded-love-domain-publication.v1"
        and report["observer_summary"] == authority["observer_summary"] == SUMMARY
        and digest(report["observer_summary"]) == digest(SUMMARY)
        and digest(report["native_calls"]) == digest(NATIVE_CALLS),
        "observer zero new calls must remain separate from78 native attempts",
    )
    require(
        tuple(report["taxa"]) == TAXA
        and report["scientific_sources"] == SCIENTIFIC_SOURCES
        and report["setting"] == SETTING
        and digest(report["setting"]) == digest(SETTING)
        and report["original_products"]
        == authority["original_products"]
        == ORIGINAL_PRODUCTS,
        "exact labelled input/profile/source and original product identities required",
    )
    require(
        len(report["parameters"]) == 30
        and tuple(r["taxon"] for r in report["parameters"]) == TAXA
        and digest(report["parameters"])
        == authority["parameters_sha256"]
        == PARAMETERS_SHA,
        "exact30 PPE/fall-speed/SD rows required",
    )
    requests = report["requests"]
    require(
        len(requests)
        == len({r["nominal_request_sha256"] for r in requests})
        == len({r["seeded_request_sha256"] for r in requests})
        == 39
        and digest(requests) == authority["requests_sha256"] == REQUESTS_SHA,
        "complete39 nominal-to-seeded identities and raw regional handoffs required",
    )
    for row in requests:
        values = row["raw_regional_cover"]
        require(
            row["nominal_request_sha256"] != row["seeded_request_sha256"]
            and type(row["root_seed"]) is int
            and row["root_seed"] == 7
            and type(row["local_seed"]) is int
            and row["local_seed"] == 3618983171
            and len(values) == 30
            and all(
                type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1
                for v in values
            )
            and abs(math.fsum(values) - 1) <= 30 * 0.000005 + 1e-12,
            "source-rounded fractions and declared local seed split required",
        )
    rows = report["ring_dispositions"]
    require(
        len(rows)
        == len({(r["seeded_request_sha256"], r["ring_index"]) for r in rows})
        == 78
        and digest(rows) == authority["ring_dispositions_sha256"] == RINGS_SHA,
        "complete78 original ring dispositions required",
    )
    expected = {(r["seeded_request_sha256"], i) for r in requests for i in (0, 1)}
    require(
        {(r["seeded_request_sha256"], r["ring_index"]) for r in rows} == expected,
        "every request requires both rings",
    )
    for row in rows:
        optimizer = row["optimizer"]
        require(
            row["status"] == "refused"
            and row["reason_code"] == "optimizer_not_converged"
            and row["candidate_is_scientific_prediction"] is False
            and row["optimizer_attempts"] == row["objective_certification_calls"] == 1
            and row["local_ring_count"] == row["ring_index"] + 1
            and row["outer_m"] == (500, 1000)[row["ring_index"]]
            and optimizer["algorithm"] == "scipy.differential_evolution"
            and optimizer["success"] is False
            and optimizer["message"] == "Evaluation budget reached"
            and optimizer["nfev"] == 16000
            and optimizer["nit"] == 52
            and optimizer["certification_nfev"] == 0
            and math.isfinite(row["certified_objective"])
            and math.isfinite(optimizer["fun"]),
            "budget refusal cannot become convergence or prediction",
        )
    require(
        report["counter_qualification"] == COUNTER_QUALIFICATION
        and report["original_nominal"] == ORIGINAL_NOMINAL
        and all(
            report[k] is False
            for k in (
                "scientific_main_return_observed",
                "predictions_scores_or_selection_admitted",
                "matched_inverse_accuracy_admitted",
            )
        )
        and authority["scientific_main_return_observed"] is False,
        "source/kernel/main-return and original native1/recovery0 limits required",
    )
    roles: dict[str, dict[str, Any]] = {
        "seeded-native-report": ORIGINAL_PRODUCTS["report.json"],
        "seeded-raw-diagnostics": ORIGINAL_PRODUCTS["seeded-diagnostics.json"],
        "seeded-trial-ledger": ORIGINAL_PRODUCTS["trials.jsonl"],
        "seeded-native-terminal": NATIVE_TERMINAL,
    }
    require(
        index
        == {
            "schema_version": "seeded-love-domain-trace-index.v1",
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
        "exact four external trace identities required",
    )
    for name in PRODUCTS:
        require(
            authority["public_products"][name] == PINS[PREFIX + name],
            "acyclic authority must bind both current products",
        )
    return {
        "requests": 39,
        "attempted_rings": 78,
        "refused_rings": 78,
        "accepted_rings": 0,
        "search_evaluations": 1248000,
        "private_trace_payloads_read": 0,
        "models_or_scores_executed": 0,
    }


def validated_seeded_love_domain(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate saved seeded LOVE evidence and declared execution bounds."""
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
        path = _regular_confined_file(repository, name, "seeded search domain")
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
