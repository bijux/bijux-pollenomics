"""Admit one completed Python comparison without rerunning source models or R."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file

PREFIX = "docs/report/method-certification/current-r-oracle/"
OWNER = "method-certification/current-r-oracle/current-python-observation"
SOURCE = "ba3a0c1da916b315eb96b7e521ebabacf4487638"
PRODUCTS = ("current-python-comparison.json", "current-python-trace-index.json")
PINS = {
    "docs/report/method-certification/current-r-oracle/current-python-comparison.json": {
        "sha256": "01bdf20cd4a1d02c1439e6042cde7eb5ba8e43b85ffbe87c3dd9b15100c0e1ec",
        "bytes": 139837,
    },
    "docs/report/method-certification/current-r-oracle/current-python-trace-index.json": {
        "sha256": "92872c5c701f54a444d03c88f23bc20ab8dfd2a83f8b1a3d73f1aedecd08d09a",
        "bytes": 20927,
    },
    "data/method-certification/native-r-finite-covariance/capture/capture.json": {
        "sha256": "008cb45fa66f8b7c96915678ee3f1ec3026924ba3fe81050ca773515e030199b",
        "bytes": 40370,
    },
}
CORE = [
    ("C0000", "K_lsm_unstable_peatland", 1e-10, 3e-10, []),
    ("C0001", "K_lsm_unstable_lake", 1e-10, 3e-10, []),
    ("C0002", "K_lsm_unstable_low_peatland", 1e-10, 3e-10, []),
    ("C0003", "K_lsm_unstable_low_lake", 1e-10, 3e-10, []),
    ("C0004", "K_gpm_neutral_peatland", 1e-10, 3e-10, []),
    ("C0005", "K_gpm_neutral_lake", 1e-10, 3e-10, []),
    ("C0006", "K_gpm_unstable_peatland", 1e-10, 3e-10, []),
    ("C0007", "K_gpm_unstable_lake", 1e-10, 3e-10, []),
    ("C0008", "K_1overd_peatland", 1e-10, 3e-10, []),
    ("C0009", "K_1overd_lake", 1e-10, 3e-10, []),
    ("C0010", "K_rounding_0.015", 0, 3e-13, []),
    ("C0011", "K_rounding_0.025", 0, 3e-13, []),
    ("C0012", "K_rounding_0.045", 0, 3e-13, []),
    ("C0013", "K_rounding_0.055", 0, 3e-13, []),
    ("C0014", "K_rounding_0.075", 0, 3e-13, []),
    ("C0015", "REVEALSinR_deterministic_1", 1e-10, 1e-10, []),
    ("C0016", "REVEALSinR_deterministic_3", 1e-10, 1e-10, []),
    ("C0017", "REVEALSinR_labels", 1e-10, 1e-10, []),
    ("C0018", "REVEALS_paired_draws", 1e-10, 1e-10, []),
    ("C0019", "lov_deterministic", 1e-10, 1e-10, []),
    ("C0020", "calK_full", 1e-10, 3e-10, []),
    ("C0021", "logeuclidean", 1e-10, 1e-10, []),
    ("C0022", "tf_objective", 1e-10, 3e-10, []),
    ("C0023", "LOVEr_deterministic", 1e-10, 3e-10, []),
    ("C0024", "LOVEoptim_candidate_replay", 1e-10, 3e-08, []),
    ("C0025", "mixed-canopy-compact_intermediates", 1e-10, 1e-10, []),
    ("C0026", "mixed-canopy-compact_taxon_axis", 0, 0, []),
    ("C0027", "mixed-canopy-compact_ring_axis", 0, 0, []),
    (
        "C0028",
        "mixed-canopy-compact_wrapper_replay",
        1e-10,
        1e-10,
        [
            611,
            612,
            613,
            614,
            616,
            617,
            618,
            619,
            621,
            622,
            623,
            624,
            626,
            627,
            628,
            629,
        ],
    ),
    ("C0029", "mixed-canopy-compact_nonfinite_objective", 1e-10, 1e-10, []),
    ("C0030", "mixed-canopy-compact_all_nonfinite_refusal", 0, 0, []),
    ("C0031", "open-land-extended_intermediates", 1e-10, 1e-10, []),
    ("C0032", "open-land-extended_taxon_axis", 0, 0, []),
    ("C0033", "open-land-extended_ring_axis", 0, 0, []),
    (
        "C0034",
        "open-land-extended_wrapper_replay",
        1e-10,
        1e-10,
        [
            733,
            734,
            735,
            736,
            738,
            739,
            740,
            741,
            743,
            744,
            745,
            746,
            748,
            749,
            750,
            751,
            753,
            754,
            755,
            756,
            758,
            759,
            760,
            761,
        ],
    ),
    ("C0035", "open-land-extended_nonfinite_objective", 1e-10, 1e-10, []),
    ("C0036", "open-land-extended_all_nonfinite_refusal", 0, 0, []),
    ("C0037", "conifer-rich-broad_intermediates", 1e-10, 1e-10, []),
    ("C0038", "conifer-rich-broad_taxon_axis", 0, 0, []),
    ("C0039", "conifer-rich-broad_ring_axis", 0, 0, []),
    (
        "C0040",
        "conifer-rich-broad_wrapper_replay",
        1e-10,
        1e-10,
        [
            916,
            917,
            918,
            919,
            921,
            922,
            923,
            924,
            926,
            927,
            928,
            929,
            931,
            932,
            933,
            934,
            936,
            937,
            938,
            939,
            941,
            942,
            943,
            944,
            946,
            947,
            948,
            949,
            951,
            952,
            953,
            954,
            956,
            957,
            958,
            959,
        ],
    ),
    ("C0041", "conifer-rich-broad_nonfinite_objective", 1e-10, 1e-10, []),
    ("C0042", "conifer-rich-broad_all_nonfinite_refusal", 0, 0, []),
]
DOMAINS = [
    "S001",
    "S002",
    "S003",
    "S004",
    "S005",
    "S006",
    "S007",
    "S008",
    "S009",
    "S010",
    "F001",
    "F002",
    "F003",
    "F004",
    "F005",
    "F006",
    "F007",
    "F008",
    "F009",
    "F010",
    "F011",
    "F012",
    "F013",
]
SUMMARY = {
    "core": {
        "cases": 43,
        "finite_numeric_pairs": 3591,
        "matching_nan_pairs": 1782,
        "maximum_absolute_error": 2.4868995751603507e-14,
        "maximum_relative_error_to_current_Python": 1.0,
        "nonfinite_mask_mismatches": 0,
        "nonidentical_finite_or_label_positions": 1926,
        "ordered_labels": 169,
        "passed": 43,
        "unequal_zero_reference_entries": 0,
        "values": 5542,
    },
    "source_domains": {
        "cases": 23,
        "finite_numeric_pairs": 274,
        "matching_nan_pairs": 12,
        "maximum_absolute_error": 5.551115123125783e-16,
        "maximum_relative_error_to_current_Python": 6.780649216896142e-13,
        "nonfinite_mask_mismatches": 0,
        "nonidentical_finite_or_label_positions": 222,
        "ordered_labels": 0,
        "passed": 23,
        "unequal_zero_reference_entries": 0,
        "values": 286,
    },
}


def require(condition: bool, reason: str) -> None:
    """Refuse retained comparison evidence outside its declared source scope."""
    if not condition:
        raise ReportRebuildError("Current Python/R observation: " + reason)


def validate_products(report: dict[str, Any], trace: dict[str, Any]) -> JsonObject:
    """Check the immutable observation; publication HEAD is a distinct epoch."""
    require(
        report["schema_version"] == "current-python-retained-R-comparison.v1"
        and report["candidate"] == trace["candidate"] == SOURCE
        and report["passed"] is True
        and report["fresh_R_executed"] is False
        and report["current_Python_executed"] is True
        and report["release_certificate"] is False
        and report["installed_first_party_claimed"] is False
        and report["new_author_numerical_calls"] == 0,
        "execution identity or scope differs",
    )
    require(
        trace["schema_version"] == "current-python-retained-R-trace-index.v1"
        and trace["summary"] == SUMMARY
        and trace["original_R"]["source_epoch"]
        == "92a0adc1f00245c1a51b4e096e1eaac4c23325e5"
        and trace["original_R"]["current_66_is_new_R_execution"] is False
        and trace["scope"]["observation_epoch_only"] == SOURCE
        and trace["scope"]["current_publication_HEAD_recomputation_claimed"] is False
        and trace["scope"]["hosted_linux_certification"] is False
        and trace["scope"]["whole_release_admitted"] is False,
        "historical/native/release scope differs",
    )
    execution = trace["execution"]["record"]
    require(
        execution["candidate"] == SOURCE
        and type(execution["native_process_exit"]) is int
        and execution["native_process_exit"] == 0
        and type(execution["collector_exit"]) is int
        and execution["collector_exit"] == 0
        and execution["timed_out"] is False
        and execution["canonical_before_after_unchanged"] is True
        and execution["report"]["sha256"] == PINS[PREFIX + PRODUCTS[0]]["sha256"]
        and execution["report"]["bytes"] == PINS[PREFIX + PRODUCTS[0]]["bytes"],
        "actual native/collector result differs",
    )
    require(
        len(report["core"]) == 43 and len(report["source_domains"]) == 23,
        "case population differs",
    )
    require(
        [
            (r["id"], r["name"], r["rtol"], r["atol"], r.get("exact_indices", []))
            for r in report["core"]
        ]
        == CORE
        and [r["id"] for r in report["source_domains"]] == DOMAINS,
        "case identity/order or original tolerance differs",
    )
    objects = trace["saved_output_objects"]
    require(
        len(objects) == trace["saved_output_object_count"] == 67
        and len({r["path"] for r in objects}) == 67,
        "saved object namespace differs",
    )
    for lane in ("core", "source_domains"):
        for row in report[lane]:
            require(row["status"] == "passed", "case did not pass")
            if lane == "source_domains":
                require(
                    row["rtol"] == 1e-10 and row["atol"] == 3e-10,
                    "domain tolerance differs",
                )
            vector = row["current_Python"]
            matches = [
                r
                for r in objects
                if r["path"].endswith("/" + Path(vector["path"]).name)
            ]
            require(
                len(matches) == 1
                and all(matches[0][k] == vector[k] for k in ("sha256", "bytes")),
                "current vector identity differs",
            )
            require(
                all(
                    row["residual_diagnostics"].get(k, True) is True
                    for k in (
                        "NaN_masks_equal",
                        "positive_infinity_masks_equal",
                        "negative_infinity_masks_equal",
                    )
                ),
                "nonfinite masks differ",
            )
    author = report["reused_author_comparison"]
    require(
        author["source_execution_candidate"]
        == "e282e08d796528488b438edd3ea661fb94b97b5d"
        and author["supported_pairs"] == 14074
        and author["original_whole_exit"] == 1
        and author["successful_R_and_Python_stages"] == [0, 0]
        and author["independent_saved_observer_exit"] == 0
        and author["new_author_numerical_calls"] == 0,
        "author scope was relabelled",
    )
    return {
        "owner_ids": [OWNER],
        "source_candidate": SOURCE,
        "current_core_cases": 43,
        "current_domain_cases": 23,
        "new_R_calls": 0,
        "new_author_calls": 0,
        "private_payloads_read": 0,
        "new_model_R_comparison_calls": 0,
        "scope": "Exact completed ba3a observation only; no future HEAD, installed, hosted, ecological or whole-release claim.",
    }


def validated_current_python_r_comparison(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate public bytes without historical source-to-future-HEAD equality."""
    selected = [r for r in owners if r.get("owner_id") == OWNER]
    if not selected and not (repository / (PREFIX + PRODUCTS[0])).exists():
        return (), {}
    require(
        len(selected) == 1
        and selected[0]["role"] == "retained_source"
        and selected[0]["paths"] == sorted(PREFIX + p for p in PRODUCTS),
        "exact separately retained owner differs",
    )
    entries = []
    values: dict[str, Any] = {}
    try:
        for name, expected in PINS.items():
            raw = _regular_confined_file(
                repository, name, "current Python/R source"
            ).read_bytes()
            require(
                hashlib.sha256(raw).hexdigest() == expected["sha256"]
                and len(raw) == expected["bytes"],
                "saved bytes differ: " + name,
            )
            if name.startswith(PREFIX):
                entry = tracked_by_path.get(name)
                require(
                    entry is not None
                    and entry.kind == "file"
                    and entry.sha256 == expected["sha256"]
                    and entry.size == len(raw),
                    "tracked saved product differs",
                )
                assert entry is not None
                entries.append(entry)
                values[name] = json.loads(raw)
        evidence = validate_products(
            values[PREFIX + PRODUCTS[0]], values[PREFIX + PRODUCTS[1]]
        )
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise ReportRebuildError(
            "Current Python/R saved observation refused"
        ) from error
    return tuple(sorted(entries, key=lambda entry: entry.path)), evidence
