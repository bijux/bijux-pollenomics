"""Admit frozen joint development choices without private scoring payload access."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.ownership import _regular_confined_file

AUTHORITY = (
    "reports/science/source-cohorts/author-love-development-setting-selection.json"
)

AUTHORITY_IDENTITIES: dict[str, Any] = {
    "observation": {
        "bytes": 3874,
        "path": "artifacts/science/development-setting-selection-output-admission/observation.json",
        "sha256": "3742fbef239c4d0b6232d357efcca388a600e4737b0433b04a893e715ec6cd3a",
    },
    "observer_execution": {
        "bytes": 1587,
        "path": "artifacts/science/development-setting-selection-output-admission/execution.json",
        "sha256": "b912b3c1c146c56ef342fffaca446b514ba07747cb94baa7cbd11c3eb83ca668",
    },
    "observer_source_review": {
        "bytes": 6243,
        "path": "artifacts/science/development-setting-selection-output-admission/source-review.json",
        "sha256": "ca306cc36756b58ed5d9a049aaf6dd9796d2283fd33a1853e76f817b087a486b",
    },
    "original_native_terminal_sha256": "b6536ddc2328cabb431800ccc019ae08bdd424adc15d7661aa0cad3bed80e313",
    "original_plan_sha256": "2169dfe9af9501c52c340f2317a5ba7a1824b135d858d48bdc78842599778cce",
    "original_products": {
        "outcome-access.jsonl": {
            "bytes": 1110,
            "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/development-setting-selection-execution/native/products/outcome-access.jsonl",
            "sha256": "4e99dcd5e97b7b835edcef45cfd0c2b8dd0ff40d28a2ed5271f06d1a44572054",
        },
        "outer-outcome-reuse.json": {
            "bytes": 1044650,
            "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/development-setting-selection-execution/native/products/outer-outcome-reuse.json",
            "sha256": "4fcd843e1a4a0946f113ca93f36d72a62664c4ce377847dae67c660378816fb0",
        },
        "report.json": {
            "bytes": 17599,
            "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/development-setting-selection-execution/native/products/report.json",
            "sha256": "73d5f944c3131b9efc855905d997b78dcb1ffcf782d412ee897a88f42930e226",
        },
        "selected-prediction-freeze.json": {
            "bytes": 932702,
            "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/development-setting-selection-execution/native/products/selected-prediction-freeze.json",
            "sha256": "1118d482a3c618463e71e86c8c54beb080902e5de8509b5194e10d49519ae759",
        },
        "selection-evidence.json": {
            "bytes": 26013616,
            "path": "/Users/bijan/bijux/bijux-pollenomics/artifacts/science/development-setting-selection-execution/native/products/selection-evidence.json",
            "sha256": "1e6982dd7775c117603ef22b3e768c8e2e4f0eefc25335ef3fa9a4e079fd18cd",
        },
    },
}

LIMITS = {
    "calibrated_uncertainty_admitted": False,
    "no_new_prediction_manifests_for_aliases": True,
    "other_windows": "TW4/TW6 are separate estimands, not joint-selection candidates. Legacy and "
    "circular diagnostics remain nonranked.",
    "previously_exposed_development": True,
    "scientific_main_return_observed": False,
    "temporal_support": "Source-declared 1250–1750 calibrated-BP TW5; reference epoch, calibration "
    "model and age uncertainty unqualified.",
    "untouched_accuracy_admitted": False,
    "vegetation_accuracy_admitted": False,
    "whole_scientific_acceptance": False,
}

OWNER = "pollen-reconstruction/author-lra-constrained/development-setting-selection/report-products"

PINS = {
    "docs/report/pollen-reconstruction/author-lra-constrained/development-setting-selection/report.json": {
        "bytes": 420378,
        "sha256": "a7d320143996c5830bda8b0a5a21547003e8f770b356c74ea8d18e6ad76727ac",
    },
    "docs/report/pollen-reconstruction/author-lra-constrained/development-setting-selection/trace-index.json": {
        "bytes": 1469,
        "sha256": "99ba7683c992b0b82237e06e9137a65fb6cbb54e7ff4cb273dc4229b38e084b0",
    },
    "reports/science/development-setting-selection/protocol.json": {
        "bytes": 44277,
        "sha256": "e0e65bb33409ff355317ce14b07fc504c11fb10d1c0fdff2e5b6d7006c9090c2",
    },
    "reports/science/development-setting-selection/source/choice.py": {
        "bytes": 9176,
        "sha256": "d3f40cf93af157cba6971d79404485834a003fd64d43c7a72bba690c0899d2e9",
    },
    "reports/science/development-setting-selection/source/replay.py": {
        "bytes": 9591,
        "sha256": "77eba1e51420e9519a28e5daa817b3d8f03eb690906458500947c1025df115ea",
    },
    "reports/science/development-setting-selection/source/sources.py": {
        "bytes": 16227,
        "sha256": "e7d709b3f0ee840c67ea9dc1615fc866dab75154addcda8fb1004e0e13c7fa46",
    },
    "reports/science/source-cohorts/author-love-development-setting-selection.json": {
        "bytes": 5102,
        "sha256": "43beb60665f4b8b9d6bb798d898895ab8667f3f17025317684b10679a99fd516",
    },
}

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/development-setting-selection/"

PROJECTION_DIGESTS = {
    "catalogue": "f7264da634e8500523371b8fc716b7b8899c5d7e67ace9b04ec7a2b9d65b8439",
    "choices": "c772e50a89297168c6eef0528ef5d96b237c989eaf7b8cd157c30e435d3cbe15",
    "freeze_ordering": "e10d565df78c228a1436c0b0dd730f162719ba96c20f8a020c42757ae8739389",
    "groups": "4fe236846a9523d5456580e1cfa88a9ffb54f9dbbf1be85525628d66309aabcf",
    "native_summary": "b28e5239629d487b89f6cc625ea4f3b8b3f692e1b9e74c16c378b01b14ff2a19",
    "observer_summary": "9bca3e7af6015b3fb5a10618bdc3ebf55563d71aa60d84c35160593ffcdbdfda",
    "original_nominal": "682e533d1b5af1fe8fe1bfb9f7536fa9236b73125d83de3aabd3cce6f0b53c79",
    "original_products": "54c7583ea573fe74002080e50a1c5b2d7bd2c2005ae1cc541723fbfd1071e6ff",
    "outcome_access": "06f74f40bd34213576e19572c716457de340370904f02c895e7ee51baaba09a2",
    "physical_inner_evidence": "72afbf1711a3307959418d34dacad3617060a609491659a4781983986d1abcde",
    "physical_outer_evidence": "07eda24bc576a2868d65c1e57f97811edccacb4e1b50f5e99d94af47b38d67dc",
    "records": "2b338a679ae8ff6168d2bacfba622fa601c7c0ace3326fe7c4344b9816a6dace",
    "scientific_limits": "304bdb2a70f35c58d05a299ecacb7c9fa25516ca468615a7a2ad9131920b7409",
    "scientific_sources": "d0073e1424726577573801f5f92adb312b3a921f284503f655abe45bb28a761d",
    "selected_outcomes": "67f68c71ad6f6aba4375e0addb54b2bf084ccbae41a1a0c848724ffad7c60a8a",
    "selected_predictions": "796d3a5e72a2f2c91e4bdc03f3fc34a9d5b94e180b99fd602c0cf81ca668f810",
    "selection_rule": "e30b0d7b2c8a4a569ba93af8fbf615f92f23112ef7d2bfa49d008d1cde890486",
    "setting_dispositions": "b773b15d6a865d073259ab6570c9a0865ea1e0f07c1ebd1ef18be2e42a80bab0",
    "source_axes": "087eb41327cf8521023fb67077f3317bd23c774e7097c91294e5bafd7f7dbc14",
    "source_equivalent_aliases": "1705b121a98889d06e007da76640aba92a0f516369190d96c7fc753d1f95f6e1",
    "taxa": "6223215ed7ffa800f190abdbff4eda970ca914ded46cced21e2a60345ba0afac",
}

SCIENTIFIC_SOURCES = {
    "reports/science/development-setting-selection/protocol.json": {
        "bytes": 44277,
        "sha256": "e0e65bb33409ff355317ce14b07fc504c11fb10d1c0fdff2e5b6d7006c9090c2",
    },
    "reports/science/development-setting-selection/source/choice.py": {
        "bytes": 9176,
        "sha256": "d3f40cf93af157cba6971d79404485834a003fd64d43c7a72bba690c0899d2e9",
    },
    "reports/science/development-setting-selection/source/replay.py": {
        "bytes": 9591,
        "sha256": "77eba1e51420e9519a28e5daa817b3d8f03eb690906458500947c1025df115ea",
    },
    "reports/science/development-setting-selection/source/sources.py": {
        "bytes": 16227,
        "sha256": "e7d709b3f0ee840c67ea9dc1615fc866dab75154addcda8fb1004e0e13c7fa46",
    },
}

SOURCE_EPOCH = "d9418b5fa1f8fc828b900b2927dd5a208ce255b6"

SUMMARY = {
    "declared_settings": 16,
    "identity_groups": 15,
    "independently_recomputed_ranking_rows": 480,
    "independently_recomputed_winners": 15,
    "new_calls": {
        "forward_calls": 0,
        "kernel_calls": 0,
        "optimizer_calls": 0,
        "scoring_calls": 0,
    },
    "nominal_inner_rows_deduplicated": 630,
    "nominal_outer_slots_deduplicated": 45,
    "outcome_access_records": 2,
    "pair_choices": 15,
    "physical_outer_slots": 315,
    "planned_inner_pair_dispositions": 6720,
    "planned_outer_pair_dispositions": 480,
    "prerequisite_refused_pairs": 8,
    "ranking_arithmetic": "Exact Fraction.from_float sum, correctly round binary64 sum then divide14; "
    "IDties preserve frozen math.fsum/14 boundary.",
    "retained_physical_inner_rows": 4410,
    "same_TW5_declared_pairs": 32,
    "selected_predictions": 15,
    "selected_refusals": 0,
    "signed_errors_RMSE_deviance": "Every saved inner/outer metric row retained byte-value-equivalent "
    "to admitted source JSON; no rescoring.",
    "source_equivalent_alias_pairs": 3,
    "unique_physical_candidate_profiles": 7,
    "unique_physical_scored_pairs": 21,
}

PRODUCTS = ("report.json", "trace-index.json")


def require(condition: bool, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not condition:
        raise ReportRebuildError("Development setting selection: " + reason)


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
        == "development-setting-selection-publication-authority.v1"
        and authority["approved"] is True
        and authority["scientific_saved_products_admitted"] is True
        and type(authority["actual_exit"]) is int
        and authority["actual_exit"] == 0
        and report["source_epoch"] == authority["source_epoch"] == SOURCE_EPOCH,
        "actual admitted saved source epoch required",
    )
    require(
        all(authority[key] == value for key, value in AUTHORITY_IDENTITIES.items())
        and authority["observation_has_aggregate_actual_exit"] is False
        and type(authority["observer_execution_actual_exit"]) is int
        and authority["observer_execution_actual_exit"] == 0,
        "raw observation and separate zero-exit execution required",
    )
    require(
        report["schema_version"] == "development-setting-selection-publication.v1"
        and digest(report["observer_summary"]) == digest(SUMMARY)
        and report["scientific_limits"] == LIMITS
        and report["scientific_sources"] == SCIENTIFIC_SOURCES,
        "complete saved selection scope and source identity required",
    )
    for key, expected in PROJECTION_DIGESTS.items():
        require(
            digest(report[key]) == authority["projection_digests"][key] == expected,
            "admitted complete " + key + " differs",
        )
    records = report["records"]
    groups = report["groups"]
    taxa = report["taxa"]
    require(
        len(records)
        == len(set(records))
        == len(groups)
        == len(set(groups.values()))
        == 15
        and set(records) == set(groups)
        and len(taxa) == len(set(taxa)) == 30,
        "exact15 development groups and30 taxa required",
    )
    catalogue = report["catalogue"]
    pairs = {(row["candidate_id"], row["spatial_id"]) for row in catalogue}
    require(
        len(catalogue) == len(pairs) == 32
        and len(report["setting_dispositions"]) == 16,
        "complete32 pair catalogue and16 setting dispositions required",
    )
    require(
        sum(row["eligibility"] == "prerequisite_refused" for row in catalogue) == 8
        and len(report["source_equivalent_aliases"]) == 3,
        "all prerequisites and source-equivalent aliases required",
    )
    choices = report["choices"]
    slots = report["selected_predictions"]
    outcomes = report["selected_outcomes"]
    require(
        len(choices) == len(slots) == len(outcomes) == 15
        and {row["outer_target"] for row in choices} == set(records)
        and {row["outer_target"] for row in slots} == set(records)
        and {row["outer_target"] for row in outcomes} == set(records),
        "all15 outer choices, frozen slots and saved outcomes required",
    )
    for choice in choices:
        ranking = choice["ranking"]
        require(
            len(ranking) == 32
            and {(row["candidate_id"], row["spatial_id"]) for row in ranking} == pairs
            and choice["status"] == "selected",
            "every declared pair must retain a ranking disposition",
        )
        selected = choice["selected_pair"]
        chosen = next(
            row
            for row in ranking
            if row["candidate_id"] == selected["candidate_id"]
            and row["spatial_id"] == selected["spatial_id"]
        )
        require(
            chosen["status"] == "complete"
            and chosen["complete_inner_predictions"]
            == chosen["expected_inner_targets"]
            == 14,
            "only complete14-inner pair may be selected",
        )
        slot = next(
            row for row in slots if row["outer_target"] == choice["outer_target"]
        )
        outcome = next(
            row for row in outcomes if row["outer_target"] == choice["outer_target"]
        )
        require(
            slot["selected_pair"] == outcome["selected_pair"] == selected
            and slot["status"] == "predicted"
            and slot["alias_creates_no_new_prediction_manifest"] is True
            and outcome["status"] == "reused_saved_score",
            "frozen source prediction and unchanged saved outcome must join",
        )
        require(
            all(
                isinstance(slot[key], str) and len(slot[key]) == 64
                for key in ("source_slot_sha256", "source_prediction_manifest_sha256")
            ),
            "original selected prediction and slot identities required",
        )
        metrics = outcome["original_score"]
        require(
            metrics["outer_target"] == choice["outer_target"]
            and metrics["baseline"] == selected["spatial_id"]
            and metrics["status"] == "scored"
            and metrics["taxon_count"] == metrics["scored_taxon_count"] == 30
            and [pair[0] for pair in metrics["signed_error_by_taxon"]] == taxa,
            "complete labelled saved metric/error/deviance population required",
        )
    inner = report["physical_inner_evidence"]
    require(
        len(inner) == 2
        and sum(row["rows"] for row in inner) == 4410
        and all(sum(row["candidate_rows"].values()) == row["rows"] for row in inner),
        "4410 physical rows must remain exact original-source references",
    )
    require(
        report["physical_outer_evidence"]["complete_score_rows"]
        == report["physical_outer_evidence"]["complete_dispositions"]
        == 315,
        "all315 original physical outer records required",
    )
    access = report["outcome_access"]
    require(
        len(access) == 2
        and all(
            row["event"] == "saved_outer_outcome_decode"
            and row["choice_freeze"]
            == report["original_products"]["selected-prediction-freeze.json"]
            for row in access
        ),
        "full persisted choice freeze before saved outer decode required",
    )
    roles = AUTHORITY_IDENTITIES["original_products"]
    require(
        index
        == {
            "schema_version": "development-setting-selection-trace-index.v1",
            "objects": [
                {
                    "sha256": row["sha256"],
                    "bytes": row["bytes"],
                    "retention_key": "sha256:" + row["sha256"],
                    "roles": [name],
                }
                for name, row in sorted(roles.items())
            ],
        },
        "exact five original external trace identities required",
    )
    require(
        all(
            authority["public_products"][name] == PINS[PREFIX + name]
            for name in PRODUCTS
        ),
        "acyclic public products required",
    )
    return {
        "declared_pairs": 32,
        "ranking_rows": 480,
        "choices": 15,
        "selected_predictions": 15,
        "selected_refusals": 0,
        "source_inner_rows_referenced": 4410,
        "new_scoring_or_model_calls": 0,
        "private_trace_payloads_read": 0,
        "untouched_accuracy_admitted": False,
    }


def validated_development_setting_selection(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate saved development choices and their exact source criteria."""
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
        path = _regular_confined_file(repository, name, "development setting selection")
        require(
            path.stat().st_nlink == 1 and path.stat().st_size == expected["bytes"],
            "physical source/product alias or size differs",
        )
        raw = path.read_bytes()
        require(
            hashlib.sha256(raw).hexdigest() == expected["sha256"],
            "current computational source/product differs",
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
